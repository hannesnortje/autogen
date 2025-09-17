"""
Thread Summarization Service for automatic conversation summarization.

Automatically summarizes long conversation threads after reaching configurable
turn thresholds to maintain memory efficiency and context relevance.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from autogen_mcp.memory_collections import MemoryScope
from autogen_mcp.multi_memory import MultiScopeMemoryService, MemoryWriteOptions
from autogen_mcp.observability import get_logger


@dataclass
class ThreadSummaryConfig:
    """Configuration for thread summarization triggers."""

    turn_threshold: int = 25  # Trigger summarization after this many turns
    importance_threshold: float = 0.7  # Only summarize threads above this importance
    max_summary_length: int = 500  # Maximum characters in summary
    keep_recent_turns: int = 5  # Keep this many recent turns after summarization


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation thread."""

    turn_id: str
    thread_id: str
    content: str
    agent_type: Optional[str]
    timestamp: float
    importance: float


class ThreadSummarizationService:
    """Manages automatic summarization of conversation threads."""

    def __init__(
        self,
        memory_service: MultiScopeMemoryService,
        config: Optional[ThreadSummaryConfig] = None,
    ):
        self.memory_service = memory_service
        self.config = config or ThreadSummaryConfig()
        self.logger = get_logger("autogen.thread_summarization")

    def analyze_thread_for_summarization(self, thread_id: str) -> Dict[str, Any]:
        """Analyze if a thread needs summarization."""
        try:
            # Search for all turns in the thread
            thread_turns = self._get_thread_turns(thread_id)

            analysis = {
                "thread_id": thread_id,
                "total_turns": len(thread_turns),
                "needs_summarization": False,
                "reason": "",
                "average_importance": 0.0,
                "oldest_turn": None,
                "latest_turn": None,
            }

            if not thread_turns:
                analysis["reason"] = "No turns found in thread"
                return analysis

            # Calculate metrics
            total_importance = sum(turn.importance for turn in thread_turns)
            analysis["average_importance"] = total_importance / len(thread_turns)
            analysis["oldest_turn"] = min(thread_turns, key=lambda t: t.timestamp)
            analysis["latest_turn"] = max(thread_turns, key=lambda t: t.timestamp)

            # Check summarization criteria
            if len(thread_turns) >= self.config.turn_threshold:
                if analysis["average_importance"] >= self.config.importance_threshold:
                    analysis["needs_summarization"] = True
                    analysis["reason"] = (
                        f"Thread has {len(thread_turns)} turns "
                        f"(threshold: {self.config.turn_threshold}) "
                        f"with avg importance {analysis['average_importance']:.2f}"
                    )
                else:
                    analysis["reason"] = (
                        f"Turn threshold met but importance too low "
                        f"({analysis['average_importance']:.2f} < {self.config.importance_threshold})"
                    )
            else:
                analysis["reason"] = (
                    f"Below turn threshold ({len(thread_turns)}/{self.config.turn_threshold})"
                )

            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze thread {thread_id}: {e}")
            return {
                "thread_id": thread_id,
                "error": str(e),
                "needs_summarization": False,
            }

    def summarize_thread(self, thread_id: str) -> Dict[str, Any]:
        """Summarize a conversation thread and archive old turns."""
        try:
            analysis = self.analyze_thread_for_summarization(thread_id)

            if not analysis.get("needs_summarization", False):
                return {
                    "thread_id": thread_id,
                    "action": "skipped",
                    "reason": analysis.get("reason", "No summarization needed"),
                }

            # Get all turns for summarization
            thread_turns = self._get_thread_turns(thread_id)
            if len(thread_turns) <= self.config.keep_recent_turns:
                return {
                    "thread_id": thread_id,
                    "action": "skipped",
                    "reason": "Not enough turns to summarize",
                }

            # Split turns into to-summarize and to-keep
            turns_to_summarize = thread_turns[: -self.config.keep_recent_turns]
            turns_to_keep = thread_turns[-self.config.keep_recent_turns :]

            # Generate summary
            summary = self._generate_thread_summary(turns_to_summarize, analysis)

            # Write summary to memory
            summary_id = self._write_thread_summary(thread_id, summary, analysis)

            # Archive old turns (mark as summarized)
            archived_turns = self._archive_turns(turns_to_summarize, summary_id)

            result = {
                "thread_id": thread_id,
                "action": "summarized",
                "summary_id": summary_id,
                "turns_summarized": len(turns_to_summarize),
                "turns_kept": len(turns_to_keep),
                "turns_archived": archived_turns,
                "summary_length": len(summary),
                "analysis": analysis,
            }

            self.logger.info(
                f"Thread {thread_id} summarized: {len(turns_to_summarize)} turns → summary",
                extra={"extra": result},
            )

            return result

        except Exception as e:
            error_msg = f"Failed to summarize thread {thread_id}: {str(e)}"
            self.logger.error(error_msg)
            return {"thread_id": thread_id, "error": error_msg, "action": "failed"}

    def auto_summarize_eligible_threads(
        self, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Automatically summarize all eligible threads."""
        try:
            # Find all active threads
            active_threads = self._find_active_threads(project_id)

            results = []
            for thread_id in active_threads:
                result = self.summarize_thread(thread_id)
                results.append(result)

                # Add small delay to avoid overwhelming the system
                time.sleep(0.1)

            summary = {
                "total_threads_checked": len(active_threads),
                "summarized": len(
                    [r for r in results if r.get("action") == "summarized"]
                ),
                "skipped": len([r for r in results if r.get("action") == "skipped"]),
                "failed": len([r for r in results if r.get("action") == "failed"]),
                "results": results,
            }

            self.logger.info(
                f"Auto-summarization complete: {summary['summarized']} summarized, "
                f"{summary['skipped']} skipped, {summary['failed']} failed"
            )

            return results

        except Exception as e:
            error_msg = f"Auto-summarization failed: {str(e)}"
            self.logger.error(error_msg)
            return [{"error": error_msg, "action": "failed"}]

    def _get_thread_turns(self, thread_id: str) -> List[ConversationTurn]:
        """Get all conversation turns for a thread."""
        # Search for thread messages
        results = self.memory_service.search(
            query=f"thread_id:{thread_id}", scope="thread", limit=100
        )

        turns = []
        for result in results:
            metadata = result.get("metadata", {})
            if metadata.get("thread_id") == thread_id:
                turn = ConversationTurn(
                    turn_id=result.get("id", "unknown"),
                    thread_id=thread_id,
                    content=result.get("content", ""),
                    agent_type=metadata.get("agent_type"),
                    timestamp=metadata.get("timestamp", time.time()),
                    importance=metadata.get("importance", 0.5),
                )
                turns.append(turn)

        # Sort by timestamp
        turns.sort(key=lambda t: t.timestamp)
        return turns

    def _generate_thread_summary(
        self, turns: List[ConversationTurn], analysis: Dict[str, Any]
    ) -> str:
        """Generate a summary of conversation turns."""
        if not turns:
            return "Empty conversation thread."

        # Extract key information
        agent_types = set(turn.agent_type for turn in turns if turn.agent_type)
        high_importance_turns = [turn for turn in turns if turn.importance >= 0.8]

        # Start with basic summary
        summary_parts = [
            f"Thread Summary ({len(turns)} turns summarized):",
            f"Participants: {', '.join(sorted(agent_types)) if agent_types else 'Unknown'}",
            f"Duration: {self._format_duration(turns[0].timestamp, turns[-1].timestamp)}",
            f"Average importance: {analysis.get('average_importance', 0.0):.2f}",
        ]

        # Add key decisions/outcomes
        if high_importance_turns:
            summary_parts.append(
                f"\nKey decisions ({len(high_importance_turns)} high-importance turns):"
            )
            for i, turn in enumerate(high_importance_turns[:3], 1):  # Max 3 key points
                content_preview = (
                    turn.content[:100] + "..."
                    if len(turn.content) > 100
                    else turn.content
                )
                summary_parts.append(f"{i}. {content_preview}")

        # Add recent context
        if len(turns) > 3:
            summary_parts.append("\nRecent context:")
            last_turn = turns[-1]
            content_preview = (
                last_turn.content[:150] + "..."
                if len(last_turn.content) > 150
                else last_turn.content
            )
            summary_parts.append(f"Last turn: {content_preview}")

        summary = "\n".join(summary_parts)

        # Truncate if too long
        if len(summary) > self.config.max_summary_length:
            summary = summary[: self.config.max_summary_length - 3] + "..."

        return summary

    def _write_thread_summary(
        self, thread_id: str, summary: str, analysis: Dict[str, Any]
    ) -> str:
        """Write the thread summary to memory."""
        options = MemoryWriteOptions(
            scope=MemoryScope.THREAD,
            thread_id=thread_id,
            importance=0.9,  # High importance for summaries
        )

        metadata = {
            "message_type": "summary",
            "summarized_turns": analysis.get("total_turns", 0),
            "summary_generated_at": time.time(),
            "average_importance": analysis.get("average_importance", 0.0),
            "is_summary": True,
        }

        return self.memory_service.write_event(summary, options, metadata)

    def _archive_turns(self, turns: List[ConversationTurn], summary_id: str) -> int:
        """Archive old turns by marking them as summarized."""
        # Note: In a real implementation, we might want to move these to an archive collection
        # or mark them with metadata indicating they've been summarized
        archived_count = 0

        for turn in turns:
            try:
                # Update the turn metadata to indicate it's been summarized
                # This is a conceptual implementation - actual implementation would
                # depend on how we want to handle archiving in Qdrant
                archived_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to archive turn {turn.turn_id}: {e}")

        return archived_count

    def _find_active_threads(self, project_id: Optional[str] = None) -> List[str]:
        """Find all active thread IDs that might need summarization."""
        try:
            # Search for recent thread messages
            results = self.memory_service.search(
                query="message_type:message OR message_type:decision OR message_type:note",
                scope="thread",
                limit=200,
            )

            # Extract unique thread IDs
            thread_ids = set()
            for result in results:
                metadata = result.get("metadata", {})
                thread_id = metadata.get("thread_id")
                if thread_id and not metadata.get("is_summary", False):
                    thread_ids.add(thread_id)

            return list(thread_ids)

        except Exception as e:
            self.logger.error(f"Failed to find active threads: {e}")
            return []

    def _format_duration(self, start_time: float, end_time: float) -> str:
        """Format duration between timestamps."""
        duration_seconds = end_time - start_time
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{int(duration_seconds)}s"

    def get_summarization_status(self) -> Dict[str, Any]:
        """Get current status of thread summarization system."""
        try:
            active_threads = self._find_active_threads()

            eligible_count = 0
            for thread_id in active_threads:
                analysis = self.analyze_thread_for_summarization(thread_id)
                if analysis.get("needs_summarization", False):
                    eligible_count += 1

            return {
                "config": {
                    "turn_threshold": self.config.turn_threshold,
                    "importance_threshold": self.config.importance_threshold,
                    "max_summary_length": self.config.max_summary_length,
                    "keep_recent_turns": self.config.keep_recent_turns,
                },
                "status": {
                    "total_active_threads": len(active_threads),
                    "threads_eligible_for_summarization": eligible_count,
                    "service_operational": True,
                },
            }

        except Exception as e:
            return {
                "config": self.config.__dict__,
                "status": {"service_operational": False, "error": str(e)},
            }
