<template>
  <div class="mycomponent-container">
    <h2>MyComponent</h2>
    <p>Vue 3 component for: Begin working on this objective: Create a simple Python hello world program that prints a greeting message. Save the program as hello.py in the working directory and make sure it works.</p>
    <div class="content">
      <button @click="handleClick" class="primary-btn">
        Click me
      </button>
      <p v-if="clicked">Button was clicked!</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const clicked = ref(false)

const handleClick = () => {
  clicked.value = true
  console.log('MyComponent button clicked')
}
</script>

<style scoped>
.mycomponent-container {
  padding: 20px;
  border-radius: 8px;
  background: #f5f5f5;
  max-width: 500px;
  margin: 0 auto;
}

.primary-btn {
  background: #42b883;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.primary-btn:hover {
  background: #369870;
}
</style>
