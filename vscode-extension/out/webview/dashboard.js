var AutoGenDashboard = (function (exports) {
    'use strict';

    /******************************************************************************
    Copyright (c) Microsoft Corporation.

    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
    REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
    AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
    INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
    LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
    OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
    PERFORMANCE OF THIS SOFTWARE.
    ***************************************************************************** */
    /* global Reflect, Promise, SuppressedError, Symbol, Iterator */


    function __decorate(decorators, target, key, desc) {
        var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
        if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
        else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
        return c > 3 && r && Object.defineProperty(target, key, r), r;
    }

    typeof SuppressedError === "function" ? SuppressedError : function (error, suppressed, message) {
        var e = new Error(message);
        return e.name = "SuppressedError", e.error = error, e.suppressed = suppressed, e;
    };

    /**
     * @license
     * Copyright 2019 Google LLC
     * SPDX-License-Identifier: BSD-3-Clause
     */
    const t$2=globalThis,e$2=t$2.ShadowRoot&&(void 0===t$2.ShadyCSS||t$2.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s$2=Symbol(),o$4=new WeakMap;let n$3 = class n{constructor(t,e,o){if(this._$cssResult$=true,o!==s$2)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e;}get styleSheet(){let t=this.o;const s=this.t;if(e$2&&void 0===t){const e=void 0!==s&&1===s.length;e&&(t=o$4.get(s)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&o$4.set(s,t));}return t}toString(){return this.cssText}};const r$4=t=>new n$3("string"==typeof t?t:t+"",void 0,s$2),i$3=(t,...e)=>{const o=1===t.length?t[0]:e.reduce(((e,s,o)=>e+(t=>{if(true===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[o+1]),t[0]);return new n$3(o,t,s$2)},S$1=(s,o)=>{if(e$2)s.adoptedStyleSheets=o.map((t=>t instanceof CSSStyleSheet?t:t.styleSheet));else for(const e of o){const o=document.createElement("style"),n=t$2.litNonce;void 0!==n&&o.setAttribute("nonce",n),o.textContent=e.cssText,s.appendChild(o);}},c$2=e$2?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return r$4(e)})(t):t;

    /**
     * @license
     * Copyright 2017 Google LLC
     * SPDX-License-Identifier: BSD-3-Clause
     */const{is:i$2,defineProperty:e$1,getOwnPropertyDescriptor:h$1,getOwnPropertyNames:r$3,getOwnPropertySymbols:o$3,getPrototypeOf:n$2}=Object,a$1=globalThis,c$1=a$1.trustedTypes,l$1=c$1?c$1.emptyScript:"",p$1=a$1.reactiveElementPolyfillSupport,d$1=(t,s)=>t,u$1={toAttribute(t,s){switch(s){case Boolean:t=t?l$1:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t);}return t},fromAttribute(t,s){let i=t;switch(s){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t);}catch(t){i=null;}}return i}},f$1=(t,s)=>!i$2(t,s),b={attribute:true,type:String,converter:u$1,reflect:false,useDefault:false,hasChanged:f$1};Symbol.metadata??=Symbol("metadata"),a$1.litPropertyMetadata??=new WeakMap;let y$1 = class y extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t);}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,s=b){if(s.state&&(s.attribute=false),this._$Ei(),this.prototype.hasOwnProperty(t)&&((s=Object.create(s)).wrapped=true),this.elementProperties.set(t,s),!s.noAccessor){const i=Symbol(),h=this.getPropertyDescriptor(t,i,s);void 0!==h&&e$1(this.prototype,t,h);}}static getPropertyDescriptor(t,s,i){const{get:e,set:r}=h$1(this.prototype,t)??{get(){return this[s]},set(t){this[s]=t;}};return {get:e,set(s){const h=e?.call(this);r?.call(this,s),this.requestUpdate(t,h,i);},configurable:true,enumerable:true}}static getPropertyOptions(t){return this.elementProperties.get(t)??b}static _$Ei(){if(this.hasOwnProperty(d$1("elementProperties")))return;const t=n$2(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties);}static finalize(){if(this.hasOwnProperty(d$1("finalized")))return;if(this.finalized=true,this._$Ei(),this.hasOwnProperty(d$1("properties"))){const t=this.properties,s=[...r$3(t),...o$3(t)];for(const i of s)this.createProperty(i,t[i]);}const t=this[Symbol.metadata];if(null!==t){const s=litPropertyMetadata.get(t);if(void 0!==s)for(const[t,i]of s)this.elementProperties.set(t,i);}this._$Eh=new Map;for(const[t,s]of this.elementProperties){const i=this._$Eu(t,s);void 0!==i&&this._$Eh.set(i,t);}this.elementStyles=this.finalizeStyles(this.styles);}static finalizeStyles(s){const i=[];if(Array.isArray(s)){const e=new Set(s.flat(1/0).reverse());for(const s of e)i.unshift(c$2(s));}else void 0!==s&&i.push(c$2(s));return i}static _$Eu(t,s){const i=s.attribute;return  false===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=false,this.hasUpdated=false,this._$Em=null,this._$Ev();}_$Ev(){this._$ES=new Promise((t=>this.enableUpdating=t)),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach((t=>t(this)));}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.();}removeController(t){this._$EO?.delete(t);}_$E_(){const t=new Map,s=this.constructor.elementProperties;for(const i of s.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t);}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return S$1(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(true),this._$EO?.forEach((t=>t.hostConnected?.()));}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach((t=>t.hostDisconnected?.()));}attributeChangedCallback(t,s,i){this._$AK(t,i);}_$ET(t,s){const i=this.constructor.elementProperties.get(t),e=this.constructor._$Eu(t,i);if(void 0!==e&&true===i.reflect){const h=(void 0!==i.converter?.toAttribute?i.converter:u$1).toAttribute(s,i.type);this._$Em=t,null==h?this.removeAttribute(e):this.setAttribute(e,h),this._$Em=null;}}_$AK(t,s){const i=this.constructor,e=i._$Eh.get(t);if(void 0!==e&&this._$Em!==e){const t=i.getPropertyOptions(e),h="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:u$1;this._$Em=e;const r=h.fromAttribute(s,t.type);this[e]=r??this._$Ej?.get(e)??r,this._$Em=null;}}requestUpdate(t,s,i){if(void 0!==t){const e=this.constructor,h=this[t];if(i??=e.getPropertyOptions(t),!((i.hasChanged??f$1)(h,s)||i.useDefault&&i.reflect&&h===this._$Ej?.get(t)&&!this.hasAttribute(e._$Eu(t,i))))return;this.C(t,s,i);} false===this.isUpdatePending&&(this._$ES=this._$EP());}C(t,s,{useDefault:i,reflect:e,wrapped:h},r){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??s??this[t]),true!==h||void 0!==r)||(this._$AL.has(t)||(this.hasUpdated||i||(s=void 0),this._$AL.set(t,s)),true===e&&this._$Em!==t&&(this._$Eq??=new Set).add(t));}async _$EP(){this.isUpdatePending=true;try{await this._$ES;}catch(t){Promise.reject(t);}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,s]of this._$Ep)this[t]=s;this._$Ep=void 0;}const t=this.constructor.elementProperties;if(t.size>0)for(const[s,i]of t){const{wrapped:t}=i,e=this[s];true!==t||this._$AL.has(s)||void 0===e||this.C(s,void 0,i,e);}}let t=false;const s=this._$AL;try{t=this.shouldUpdate(s),t?(this.willUpdate(s),this._$EO?.forEach((t=>t.hostUpdate?.())),this.update(s)):this._$EM();}catch(s){throw t=false,this._$EM(),s}t&&this._$AE(s);}willUpdate(t){}_$AE(t){this._$EO?.forEach((t=>t.hostUpdated?.())),this.hasUpdated||(this.hasUpdated=true,this.firstUpdated(t)),this.updated(t);}_$EM(){this._$AL=new Map,this.isUpdatePending=false;}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return  true}update(t){this._$Eq&&=this._$Eq.forEach((t=>this._$ET(t,this[t]))),this._$EM();}updated(t){}firstUpdated(t){}};y$1.elementStyles=[],y$1.shadowRootOptions={mode:"open"},y$1[d$1("elementProperties")]=new Map,y$1[d$1("finalized")]=new Map,p$1?.({ReactiveElement:y$1}),(a$1.reactiveElementVersions??=[]).push("2.1.1");

    /**
     * @license
     * Copyright 2017 Google LLC
     * SPDX-License-Identifier: BSD-3-Clause
     */
    const t$1=globalThis,i$1=t$1.trustedTypes,s$1=i$1?i$1.createPolicy("lit-html",{createHTML:t=>t}):void 0,e="$lit$",h=`lit$${Math.random().toFixed(9).slice(2)}$`,o$2="?"+h,n$1=`<${o$2}>`,r$2=document,l=()=>r$2.createComment(""),c=t=>null===t||"object"!=typeof t&&"function"!=typeof t,a=Array.isArray,u=t=>a(t)||"function"==typeof t?.[Symbol.iterator],d="[ \t\n\f\r]",f=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,v=/-->/g,_=/>/g,m=RegExp(`>|${d}(?:([^\\s"'>=/]+)(${d}*=${d}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),p=/'/g,g=/"/g,$=/^(?:script|style|textarea|title)$/i,y=t=>(i,...s)=>({_$litType$:t,strings:i,values:s}),x=y(1),T=Symbol.for("lit-noChange"),E=Symbol.for("lit-nothing"),A=new WeakMap,C=r$2.createTreeWalker(r$2,129);function P(t,i){if(!a(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==s$1?s$1.createHTML(i):i}const V=(t,i)=>{const s=t.length-1,o=[];let r,l=2===i?"<svg>":3===i?"<math>":"",c=f;for(let i=0;i<s;i++){const s=t[i];let a,u,d=-1,y=0;for(;y<s.length&&(c.lastIndex=y,u=c.exec(s),null!==u);)y=c.lastIndex,c===f?"!--"===u[1]?c=v:void 0!==u[1]?c=_:void 0!==u[2]?($.test(u[2])&&(r=RegExp("</"+u[2],"g")),c=m):void 0!==u[3]&&(c=m):c===m?">"===u[0]?(c=r??f,d=-1):void 0===u[1]?d=-2:(d=c.lastIndex-u[2].length,a=u[1],c=void 0===u[3]?m:'"'===u[3]?g:p):c===g||c===p?c=m:c===v||c===_?c=f:(c=m,r=void 0);const x=c===m&&t[i+1].startsWith("/>")?" ":"";l+=c===f?s+n$1:d>=0?(o.push(a),s.slice(0,d)+e+s.slice(d)+h+x):s+h+(-2===d?i:x);}return [P(t,l+(t[s]||"<?>")+(2===i?"</svg>":3===i?"</math>":"")),o]};class N{constructor({strings:t,_$litType$:s},n){let r;this.parts=[];let c=0,a=0;const u=t.length-1,d=this.parts,[f,v]=V(t,s);if(this.el=N.createElement(f,n),C.currentNode=this.el.content,2===s||3===s){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes);}for(;null!==(r=C.nextNode())&&d.length<u;){if(1===r.nodeType){if(r.hasAttributes())for(const t of r.getAttributeNames())if(t.endsWith(e)){const i=v[a++],s=r.getAttribute(t).split(h),e=/([.?@])?(.*)/.exec(i);d.push({type:1,index:c,name:e[2],strings:s,ctor:"."===e[1]?H:"?"===e[1]?I:"@"===e[1]?L:k}),r.removeAttribute(t);}else t.startsWith(h)&&(d.push({type:6,index:c}),r.removeAttribute(t));if($.test(r.tagName)){const t=r.textContent.split(h),s=t.length-1;if(s>0){r.textContent=i$1?i$1.emptyScript:"";for(let i=0;i<s;i++)r.append(t[i],l()),C.nextNode(),d.push({type:2,index:++c});r.append(t[s],l());}}}else if(8===r.nodeType)if(r.data===o$2)d.push({type:2,index:c});else {let t=-1;for(;-1!==(t=r.data.indexOf(h,t+1));)d.push({type:7,index:c}),t+=h.length-1;}c++;}}static createElement(t,i){const s=r$2.createElement("template");return s.innerHTML=t,s}}function S(t,i,s=t,e){if(i===T)return i;let h=void 0!==e?s._$Co?.[e]:s._$Cl;const o=c(i)?void 0:i._$litDirective$;return h?.constructor!==o&&(h?._$AO?.(false),void 0===o?h=void 0:(h=new o(t),h._$AT(t,s,e)),void 0!==e?(s._$Co??=[])[e]=h:s._$Cl=h),void 0!==h&&(i=S(t,h._$AS(t,i.values),h,e)),i}class M{constructor(t,i){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=i;}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:i},parts:s}=this._$AD,e=(t?.creationScope??r$2).importNode(i,true);C.currentNode=e;let h=C.nextNode(),o=0,n=0,l=s[0];for(;void 0!==l;){if(o===l.index){let i;2===l.type?i=new R(h,h.nextSibling,this,t):1===l.type?i=new l.ctor(h,l.name,l.strings,this,t):6===l.type&&(i=new z(h,this,t)),this._$AV.push(i),l=s[++n];}o!==l?.index&&(h=C.nextNode(),o++);}return C.currentNode=r$2,e}p(t){let i=0;for(const s of this._$AV) void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,i),i+=s.strings.length-2):s._$AI(t[i])),i++;}}class R{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,i,s,e){this.type=2,this._$AH=E,this._$AN=void 0,this._$AA=t,this._$AB=i,this._$AM=s,this.options=e,this._$Cv=e?.isConnected??true;}get parentNode(){let t=this._$AA.parentNode;const i=this._$AM;return void 0!==i&&11===t?.nodeType&&(t=i.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,i=this){t=S(this,t,i),c(t)?t===E||null==t||""===t?(this._$AH!==E&&this._$AR(),this._$AH=E):t!==this._$AH&&t!==T&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):u(t)?this.k(t):this._(t);}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t));}_(t){this._$AH!==E&&c(this._$AH)?this._$AA.nextSibling.data=t:this.T(r$2.createTextNode(t)),this._$AH=t;}$(t){const{values:i,_$litType$:s}=t,e="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=N.createElement(P(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===e)this._$AH.p(i);else {const t=new M(e,this),s=t.u(this.options);t.p(i),this.T(s),this._$AH=t;}}_$AC(t){let i=A.get(t.strings);return void 0===i&&A.set(t.strings,i=new N(t)),i}k(t){a(this._$AH)||(this._$AH=[],this._$AR());const i=this._$AH;let s,e=0;for(const h of t)e===i.length?i.push(s=new R(this.O(l()),this.O(l()),this,this.options)):s=i[e],s._$AI(h),e++;e<i.length&&(this._$AR(s&&s._$AB.nextSibling,e),i.length=e);}_$AR(t=this._$AA.nextSibling,i){for(this._$AP?.(false,true,i);t!==this._$AB;){const i=t.nextSibling;t.remove(),t=i;}}setConnected(t){ void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t));}}class k{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,i,s,e,h){this.type=1,this._$AH=E,this._$AN=void 0,this.element=t,this.name=i,this._$AM=e,this.options=h,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=E;}_$AI(t,i=this,s,e){const h=this.strings;let o=false;if(void 0===h)t=S(this,t,i,0),o=!c(t)||t!==this._$AH&&t!==T,o&&(this._$AH=t);else {const e=t;let n,r;for(t=h[0],n=0;n<h.length-1;n++)r=S(this,e[s+n],i,n),r===T&&(r=this._$AH[n]),o||=!c(r)||r!==this._$AH[n],r===E?t=E:t!==E&&(t+=(r??"")+h[n+1]),this._$AH[n]=r;}o&&!e&&this.j(t);}j(t){t===E?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"");}}class H extends k{constructor(){super(...arguments),this.type=3;}j(t){this.element[this.name]=t===E?void 0:t;}}class I extends k{constructor(){super(...arguments),this.type=4;}j(t){this.element.toggleAttribute(this.name,!!t&&t!==E);}}class L extends k{constructor(t,i,s,e,h){super(t,i,s,e,h),this.type=5;}_$AI(t,i=this){if((t=S(this,t,i,0)??E)===T)return;const s=this._$AH,e=t===E&&s!==E||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,h=t!==E&&(s===E||e);e&&this.element.removeEventListener(this.name,this,s),h&&this.element.addEventListener(this.name,this,t),this._$AH=t;}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t);}}class z{constructor(t,i,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=i,this.options=s;}get _$AU(){return this._$AM._$AU}_$AI(t){S(this,t);}}const j=t$1.litHtmlPolyfillSupport;j?.(N,R),(t$1.litHtmlVersions??=[]).push("3.3.1");const B=(t,i,s)=>{const e=s?.renderBefore??i;let h=e._$litPart$;if(void 0===h){const t=s?.renderBefore??null;e._$litPart$=h=new R(i.insertBefore(l(),t),t,void 0,s??{});}return h._$AI(t),h};

    /**
     * @license
     * Copyright 2017 Google LLC
     * SPDX-License-Identifier: BSD-3-Clause
     */const s=globalThis;class i extends y$1{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0;}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const r=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=B(r,this.renderRoot,this.renderOptions);}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(true);}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(false);}render(){return T}}i._$litElement$=true,i["finalized"]=true,s.litElementHydrateSupport?.({LitElement:i});const o$1=s.litElementPolyfillSupport;o$1?.({LitElement:i});(s.litElementVersions??=[]).push("4.2.1");

    /**
     * @license
     * Copyright 2017 Google LLC
     * SPDX-License-Identifier: BSD-3-Clause
     */
    const t=t=>(e,o)=>{ void 0!==o?o.addInitializer((()=>{customElements.define(t,e);})):customElements.define(t,e);};

    /**
     * @license
     * Copyright 2017 Google LLC
     * SPDX-License-Identifier: BSD-3-Clause
     */const o={attribute:true,type:String,converter:u$1,reflect:false,hasChanged:f$1},r$1=(t=o,e,r)=>{const{kind:n,metadata:i}=r;let s=globalThis.litPropertyMetadata.get(i);if(void 0===s&&globalThis.litPropertyMetadata.set(i,s=new Map),"setter"===n&&((t=Object.create(t)).wrapped=true),s.set(r.name,t),"accessor"===n){const{name:o}=r;return {set(r){const n=e.get.call(this);e.set.call(this,r),this.requestUpdate(o,n,t);},init(e){return void 0!==e&&this.C(o,void 0,t,e),e}}}if("setter"===n){const{name:o}=r;return function(r){const n=this[o];e.call(this,r),this.requestUpdate(o,n,t);}}throw Error("Unsupported decorator location: "+n)};function n(t){return (e,o)=>"object"==typeof o?r$1(t,e,o):((t,e,o)=>{const r=e.hasOwnProperty(o);return e.constructor.createProperty(o,t),r?Object.getOwnPropertyDescriptor(e,o):void 0})(t,e,o)}

    /**
     * @license
     * Copyright 2017 Google LLC
     * SPDX-License-Identifier: BSD-3-Clause
     */function r(r){return n({...r,state:true,attribute:false})}

    /**
     * Base component class for all AutoGen Lit 3 components
     * Provides common functionality and VS Code theme integration
     */
    class BaseComponent extends i {
        constructor() {
            super(...arguments);
            /**
             * Loading state for the component
             */
            this._loading = false;
            /**
             * Error state for the component
             */
            this._error = null;
        }
        /**
         * Common VS Code theme styles
         */
        static { this.baseStyles = i$3 `
    :host {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      font-weight: var(--vscode-font-weight);
      color: var(--vscode-foreground);
      background-color: var(--vscode-editor-background);
    }

    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      opacity: 0.7;
    }

    .error {
      padding: 16px;
      margin: 8px 0;
      background-color: var(--vscode-inputValidation-errorBackground);
      border: 1px solid var(--vscode-inputValidation-errorBorder);
      border-radius: 4px;
      color: var(--vscode-inputValidation-errorForeground);
    }

    .hidden {
      display: none !important;
    }

    .btn {
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-size: var(--vscode-font-size);
      font-family: var(--vscode-font-family);
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background-color 0.1s ease;
    }

    .btn:hover {
      background-color: var(--vscode-button-hoverBackground);
    }

    .btn:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .btn.secondary {
      background-color: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
    }

    .btn.secondary:hover {
      background-color: var(--vscode-button-secondaryHoverBackground);
    }

    .input {
      background-color: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border);
      border-radius: 2px;
      padding: 6px 8px;
      font-size: var(--vscode-font-size);
      font-family: var(--vscode-font-family);
      width: 100%;
      box-sizing: border-box;
    }

    .input:focus {
      outline: none;
      border-color: var(--vscode-inputOption-activeBorder);
      box-shadow: 0 0 0 1px var(--vscode-inputOption-activeBorder);
    }

    .input::placeholder {
      color: var(--vscode-input-placeholderForeground);
    }
  `; }
        /**
         * Combine base styles with component-specific styles
         */
        static get styles() {
            return [this.baseStyles];
        }
        /**
         * Set loading state
         */
        setLoading(loading) {
            this._loading = loading;
            this.requestUpdate();
        }
        /**
         * Set error state
         */
        setError(error) {
            this._error = error;
            this.requestUpdate();
        }
        /**
         * Clear error state
         */
        clearError() {
            this._error = null;
            this.requestUpdate();
        }
        /**
         * Dispatch a custom event with proper typing
         */
        dispatchCustomEvent(type, detail, options) {
            const event = new CustomEvent(type, {
                detail,
                bubbles: true,
                composed: true,
                ...options
            });
            this.dispatchEvent(event);
        }
        /**
         * Render loading spinner
         */
        renderLoading() {
            return x `
      <div class="loading">
        <span>Loading...</span>
      </div>
    `;
        }
        /**
         * Render error message
         */
        renderError() {
            if (!this._error)
                return x ``;
            return x `
      <div class="error">
        <strong>Error:</strong> ${this._error}
        <button class="btn secondary" @click="${this.clearError}" style="margin-left: 8px; padding: 4px 8px;">
          Dismiss
        </button>
      </div>
    `;
        }
        /**
         * Handle promise with loading and error states
         */
        async handleAsync(promise, errorPrefix = 'Operation failed') {
            try {
                this.setLoading(true);
                this.clearError();
                const result = await promise;
                return result;
            }
            catch (error) {
                const message = error instanceof Error ? error.message : String(error);
                this.setError(`${errorPrefix}: ${message}`);
                return null;
            }
            finally {
                this.setLoading(false);
            }
        }
        /**
         * Lifecycle: Component connected to DOM
         */
        connectedCallback() {
            super.connectedCallback();
            this.addEventListener('error', this._handleGlobalError.bind(this));
        }
        /**
         * Lifecycle: Component disconnected from DOM
         */
        disconnectedCallback() {
            super.disconnectedCallback();
            this.removeEventListener('error', this._handleGlobalError.bind(this));
        }
        /**
         * Global error handler
         */
        _handleGlobalError(event) {
            console.error('Component error:', event.error);
            this.setError(`Unexpected error: ${event.error?.message || 'Unknown error'}`);
        }
    }
    __decorate([
        r()
    ], BaseComponent.prototype, "_loading", void 0);
    __decorate([
        r()
    ], BaseComponent.prototype, "_error", void 0);

    /**
     * Base panel component for main dashboard panels
     * Provides common panel functionality, header, actions, and content area
     */
    class BasePanel extends BaseComponent {
        constructor() {
            super(...arguments);
            /**
             * Panel title displayed in header
             */
            this.title = '';
            /**
             * Panel subtitle or description
             */
            this.subtitle = '';
            /**
             * Whether the panel can be refreshed
             */
            this.refreshable = true;
            /**
             * Whether the panel can be collapsed
             */
            this.collapsible = false;
            /**
             * Collapsed state
             */
            this._collapsed = false;
        }
        /**
         * Panel-specific styles
         */
        static { this.panelStyles = i$3 `
    :host {
      display: block;
      background-color: var(--vscode-editor-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
      overflow: hidden;
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      background-color: var(--vscode-titleBar-inactiveBackground);
      border-bottom: 1px solid var(--vscode-panel-border);
    }

    .panel-title-section {
      flex: 1;
      min-width: 0;
    }

    .panel-title {
      font-size: 18px;
      font-weight: 600;
      margin: 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .panel-subtitle {
      font-size: 13px;
      margin: 4px 0 0 0;
      color: var(--vscode-descriptionForeground);
      opacity: 0.8;
    }

    .panel-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .panel-content {
      padding: 20px;
      min-height: 200px;
    }

    .panel-content.collapsed {
      display: none;
    }

    .action-button {
      background: none;
      border: none;
      color: var(--vscode-titleBar-activeForeground);
      cursor: pointer;
      padding: 6px;
      border-radius: 3px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .action-button:hover {
      background-color: var(--vscode-toolbar-hoverBackground);
    }

    .action-button:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .expand-icon {
      transition: transform 0.2s ease;
    }

    .expand-icon.collapsed {
      transform: rotate(-90deg);
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 40px 20px;
      text-align: center;
      opacity: 0.6;
    }

    .empty-state-icon {
      font-size: 48px;
      margin-bottom: 16px;
      opacity: 0.5;
    }

    .empty-state-title {
      font-size: 16px;
      font-weight: 500;
      margin: 0 0 8px 0;
    }

    .empty-state-description {
      font-size: 14px;
      margin: 0 0 16px 0;
      max-width: 300px;
    }
  `; }
        static get styles() {
            return [super.styles, this.panelStyles];
        }
        /**
         * Render panel actions (refresh, collapse, etc.)
         * Can be overridden by extending classes
         */
        renderActions() {
            return x `
      ${this.refreshable ? x `
        <button
          class="action-button"
          title="Refresh"
          @click="${this._handleRefresh}"
          ?disabled="${this._loading}"
        >
          🔄
        </button>
      ` : ''}
      
      ${this.collapsible ? x `
        <button
          class="action-button"
          title="${this._collapsed ? 'Expand' : 'Collapse'}"
          @click="${this._toggleCollapsed}"
        >
          <span class="expand-icon ${this._collapsed ? 'collapsed' : ''}">
            ▼
          </span>
        </button>
      ` : ''}
    `;
        }
        /**
         * Render empty state when no content is available
         * Can be overridden by extending classes
         */
        renderEmptyState(title = 'No data available', description = 'There is nothing to display at the moment.', icon = '📭') {
            return x `
      <div class="empty-state">
        <div class="empty-state-icon">${icon}</div>
        <div class="empty-state-title">${title}</div>
        <div class="empty-state-description">${description}</div>
        ${this.renderEmptyStateActions()}
      </div>
    `;
        }
        /**
         * Render actions for empty state
         * Can be overridden by extending classes
         */
        renderEmptyStateActions() {
            return x ``;
        }
        /**
         * Main render method
         */
        render() {
            return x `
      <div class="panel-header">
        <div class="panel-title-section">
          <h2 class="panel-title">${this.title}</h2>
          ${this.subtitle ? x `
            <p class="panel-subtitle">${this.subtitle}</p>
          ` : ''}
        </div>
        <div class="panel-actions">
          ${this.renderActions()}
        </div>
      </div>

      <div class="panel-content ${this._collapsed ? 'collapsed' : ''}">
        ${this.renderError()}
        ${this._loading ? this.renderLoading() : this.renderContent()}
      </div>
    `;
        }
        /**
         * Handle refresh action
         * Can be overridden by extending classes
         */
        async _handleRefresh() {
            this.dispatchCustomEvent('panel-refresh', {
                panelType: this.tagName.toLowerCase()
            });
            // Override this method in extending classes to implement actual refresh logic
            await this.onRefresh();
        }
        /**
         * Refresh hook for extending classes
         */
        async onRefresh() {
            // Default implementation - can be overridden
        }
        /**
         * Toggle collapsed state
         */
        _toggleCollapsed() {
            this._collapsed = !this._collapsed;
            this.dispatchCustomEvent('panel-toggle', {
                panelType: this.tagName.toLowerCase(),
                collapsed: this._collapsed
            });
        }
        /**
         * Programmatically set collapsed state
         */
        setCollapsed(collapsed) {
            this._collapsed = collapsed;
            this.requestUpdate();
        }
        /**
         * Get current collapsed state
         */
        get collapsed() {
            return this._collapsed;
        }
    }
    __decorate([
        n({ type: String })
    ], BasePanel.prototype, "title", void 0);
    __decorate([
        n({ type: String })
    ], BasePanel.prototype, "subtitle", void 0);
    __decorate([
        n({ type: Boolean })
    ], BasePanel.prototype, "refreshable", void 0);
    __decorate([
        n({ type: Boolean })
    ], BasePanel.prototype, "collapsible", void 0);
    __decorate([
        r()
    ], BasePanel.prototype, "_collapsed", void 0);

    /**
     * Shared CSS styles for AutoGen extension components
     * Provides consistent styling and VS Code theme integration
     */
    /**
     * VS Code theme CSS custom properties
     * These are automatically populated by VS Code's webview context
     */
    const vscodeThemeVariables = i$3 `
  :host {
    /* Fonts */
    --vscode-font-family: var(--vscode-font-family, 'Segoe WPC', 'Segoe UI', sans-serif);
    --vscode-font-size: var(--vscode-font-size, 13px);
    --vscode-font-weight: var(--vscode-font-weight, normal);
    --vscode-editor-font-family: var(--vscode-editor-font-family, 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace);
    
    /* Colors - Background */
    --vscode-foreground: var(--vscode-foreground, #cccccc);
    --vscode-background: var(--vscode-background, #1e1e1e);
    --vscode-editor-background: var(--vscode-editor-background, #1e1e1e);
    --vscode-editor-foreground: var(--vscode-editor-foreground, #d4d4d4);
    
    /* Colors - UI Elements */
    --vscode-titleBar-activeForeground: var(--vscode-titleBar-activeForeground, #cccccc);
    --vscode-titleBar-inactiveBackground: var(--vscode-titleBar-inactiveBackground, #3c3c3c);
    --vscode-descriptionForeground: var(--vscode-descriptionForeground, #cccccc99);
    
    /* Colors - Buttons */
    --vscode-button-background: var(--vscode-button-background, #0e639c);
    --vscode-button-foreground: var(--vscode-button-foreground, #ffffff);
    --vscode-button-hoverBackground: var(--vscode-button-hoverBackground, #1177bb);
    --vscode-button-secondaryBackground: var(--vscode-button-secondaryBackground, #5a5d5e);
    --vscode-button-secondaryForeground: var(--vscode-button-secondaryForeground, #ffffff);
    --vscode-button-secondaryHoverBackground: var(--vscode-button-secondaryHoverBackground, #666868);
    
    /* Colors - Input */
    --vscode-input-background: var(--vscode-input-background, #3c3c3c);
    --vscode-input-foreground: var(--vscode-input-foreground, #cccccc);
    --vscode-input-border: var(--vscode-input-border, #3c3c3c);
    --vscode-input-placeholderForeground: var(--vscode-input-placeholderForeground, #cccccc80);
    --vscode-inputOption-activeBorder: var(--vscode-inputOption-activeBorder, #007acc);
    
    /* Colors - Validation */
    --vscode-inputValidation-errorBackground: var(--vscode-inputValidation-errorBackground, #5a1d1d);
    --vscode-inputValidation-errorBorder: var(--vscode-inputValidation-errorBorder, #be1100);
    --vscode-inputValidation-errorForeground: var(--vscode-inputValidation-errorForeground, #f48771);
    --vscode-inputValidation-warningBackground: var(--vscode-inputValidation-warningBackground, #352a05);
    --vscode-inputValidation-warningBorder: var(--vscode-inputValidation-warningBorder, #cc6d00);
    --vscode-inputValidation-warningForeground: var(--vscode-inputValidation-warningForeground, #ffcc00);
    
    /* Colors - Panel */
    --vscode-panel-background: var(--vscode-panel-background, #1e1e1e);
    --vscode-panel-border: var(--vscode-panel-border, #454545);
    --vscode-panelTitle-activeForeground: var(--vscode-panelTitle-activeForeground, #e7e7e7);
    --vscode-panelTitle-inactiveForeground: var(--vscode-panelTitle-inactiveForeground, #e7e7e799);
    
    /* Colors - List & Tree */
    --vscode-list-activeSelectionBackground: var(--vscode-list-activeSelectionBackground, #094771);
    --vscode-list-activeSelectionForeground: var(--vscode-list-activeSelectionForeground, #ffffff);
    --vscode-list-hoverBackground: var(--vscode-list-hoverBackground, #2a2d2e);
    --vscode-list-focusBackground: var(--vscode-list-focusBackground, #062f4a);
    
    /* Colors - Status */
    --vscode-errorForeground: var(--vscode-errorForeground, #f48771);
    --vscode-warningForeground: var(--vscode-warningForeground, #ffcc00);
    --vscode-charts-green: var(--vscode-charts-green, #89d185);
    --vscode-charts-red: var(--vscode-charts-red, #f48771);
    --vscode-charts-yellow: var(--vscode-charts-yellow, #ffcc00);
    --vscode-charts-blue: var(--vscode-charts-blue, #75beff);
    
    /* Colors - Toolbar */
    --vscode-toolbar-hoverBackground: var(--vscode-toolbar-hoverBackground, #5a5d5e14);
    --vscode-toolbar-activeBackground: var(--vscode-toolbar-activeBackground, #5a5d5e28);
    
    /* Colors - Badge */
    --vscode-badge-background: var(--vscode-badge-background, #4d4d4d);
    --vscode-badge-foreground: var(--vscode-badge-foreground, #ffffff);
    
    /* Colors - Progress */
    --vscode-progressBar-background: var(--vscode-progressBar-background, #0e639c);
  }
`;
    /**
     * Common layout utilities
     */
    const layoutStyles = i$3 `
  .flex {
    display: flex;
  }

  .flex-column {
    display: flex;
    flex-direction: column;
  }

  .flex-row {
    display: flex;
    flex-direction: row;
  }

  .flex-center {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .flex-between {
    display: flex;
    justify-content: space-between;
  }

  .flex-start {
    display: flex;
    justify-content: flex-start;
  }

  .flex-end {
    display: flex;
    justify-content: flex-end;
  }

  .flex-wrap {
    flex-wrap: wrap;
  }

  .flex-nowrap {
    flex-wrap: nowrap;
  }

  .flex-grow {
    flex-grow: 1;
  }

  .flex-shrink {
    flex-shrink: 1;
  }

  .align-center {
    align-items: center;
  }

  .align-start {
    align-items: flex-start;
  }

  .align-end {
    align-items: flex-end;
  }

  .gap-xs { gap: 4px; }
  .gap-sm { gap: 8px; }
  .gap-md { gap: 12px; }
  .gap-lg { gap: 16px; }
  .gap-xl { gap: 24px; }
`;
    /**
     * Spacing utilities
     */
    const spacingStyles = i$3 `
  .m-0 { margin: 0; }
  .m-xs { margin: 4px; }
  .m-sm { margin: 8px; }
  .m-md { margin: 12px; }
  .m-lg { margin: 16px; }
  .m-xl { margin: 24px; }

  .mt-0 { margin-top: 0; }
  .mt-xs { margin-top: 4px; }
  .mt-sm { margin-top: 8px; }
  .mt-md { margin-top: 12px; }
  .mt-lg { margin-top: 16px; }
  .mt-xl { margin-top: 24px; }

  .mb-0 { margin-bottom: 0; }
  .mb-xs { margin-bottom: 4px; }
  .mb-sm { margin-bottom: 8px; }
  .mb-md { margin-bottom: 12px; }
  .mb-lg { margin-bottom: 16px; }
  .mb-xl { margin-bottom: 24px; }

  .ml-0 { margin-left: 0; }
  .ml-xs { margin-left: 4px; }
  .ml-sm { margin-left: 8px; }
  .ml-md { margin-left: 12px; }
  .ml-lg { margin-left: 16px; }
  .ml-xl { margin-left: 24px; }

  .mr-0 { margin-right: 0; }
  .mr-xs { margin-right: 4px; }
  .mr-sm { margin-right: 8px; }
  .mr-md { margin-right: 12px; }
  .mr-lg { margin-right: 16px; }
  .mr-xl { margin-right: 24px; }

  .p-0 { padding: 0; }
  .p-xs { padding: 4px; }
  .p-sm { padding: 8px; }
  .p-md { padding: 12px; }
  .p-lg { padding: 16px; }
  .p-xl { padding: 24px; }

  .pt-0 { padding-top: 0; }
  .pt-xs { padding-top: 4px; }
  .pt-sm { padding-top: 8px; }
  .pt-md { padding-top: 12px; }
  .pt-lg { padding-top: 16px; }
  .pt-xl { padding-top: 24px; }

  .pb-0 { padding-bottom: 0; }
  .pb-xs { padding-bottom: 4px; }
  .pb-sm { padding-bottom: 8px; }
  .pb-md { padding-bottom: 12px; }
  .pb-lg { padding-bottom: 16px; }
  .pb-xl { padding-bottom: 24px; }

  .pl-0 { padding-left: 0; }
  .pl-xs { padding-left: 4px; }
  .pl-sm { padding-left: 8px; }
  .pl-md { padding-left: 12px; }
  .pl-lg { padding-left: 16px; }
  .pl-xl { padding-left: 24px; }

  .pr-0 { padding-right: 0; }
  .pr-xs { padding-right: 4px; }
  .pr-sm { padding-right: 8px; }
  .pr-md { padding-right: 12px; }
  .pr-lg { padding-right: 16px; }
  .pr-xl { padding-right: 24px; }
`;
    /**
     * Typography utilities
     */
    const typographyStyles = i$3 `
  .text-xs { font-size: 11px; }
  .text-sm { font-size: 12px; }
  .text-base { font-size: var(--vscode-font-size, 13px); }
  .text-lg { font-size: 14px; }
  .text-xl { font-size: 16px; }
  .text-2xl { font-size: 18px; }
  .text-3xl { font-size: 20px; }
  .text-4xl { font-size: 24px; }

  .font-light { font-weight: 300; }
  .font-normal { font-weight: normal; }
  .font-medium { font-weight: 500; }
  .font-semibold { font-weight: 600; }
  .font-bold { font-weight: bold; }

  .text-left { text-align: left; }
  .text-center { text-align: center; }
  .text-right { text-align: right; }

  .text-truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .text-wrap {
    white-space: normal;
    word-wrap: break-word;
  }

  .text-nowrap {
    white-space: nowrap;
  }

  .text-uppercase {
    text-transform: uppercase;
  }

  .text-lowercase {
    text-transform: lowercase;
  }

  .text-capitalize {
    text-transform: capitalize;
  }
`;
    /**
     * State and interaction utilities
     */
    const stateStyles = i$3 `
  .hidden {
    display: none !important;
  }

  .invisible {
    visibility: hidden;
  }

  .opacity-0 { opacity: 0; }
  .opacity-25 { opacity: 0.25; }
  .opacity-50 { opacity: 0.5; }
  .opacity-75 { opacity: 0.75; }
  .opacity-100 { opacity: 1; }

  .pointer-events-none {
    pointer-events: none;
  }

  .pointer-events-auto {
    pointer-events: auto;
  }

  .cursor-pointer {
    cursor: pointer;
  }

  .cursor-not-allowed {
    cursor: not-allowed;
  }

  .cursor-default {
    cursor: default;
  }

  .select-none {
    user-select: none;
  }

  .select-text {
    user-select: text;
  }

  .select-all {
    user-select: all;
  }
`;
    /**
     * Common component styles
     */
    const componentStyles = i$3 `
  /* Card-like containers */
  .card {
    background-color: var(--vscode-editor-background);
    border: 1px solid var(--vscode-panel-border);
    border-radius: 4px;
    overflow: hidden;
  }

  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--vscode-panel-border);
    background-color: var(--vscode-titleBar-inactiveBackground);
  }

  .card-body {
    padding: 20px;
  }

  .card-footer {
    padding: 16px 20px;
    border-top: 1px solid var(--vscode-panel-border);
    background-color: var(--vscode-titleBar-inactiveBackground);
  }

  /* Dividers */
  .divider {
    height: 1px;
    background-color: var(--vscode-panel-border);
    margin: 16px 0;
  }

  .divider-vertical {
    width: 1px;
    background-color: var(--vscode-panel-border);
    margin: 0 16px;
  }

  /* Status indicators */
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
  }

  .status-dot.success {
    background-color: var(--vscode-charts-green);
  }

  .status-dot.error {
    background-color: var(--vscode-charts-red);
  }

  .status-dot.warning {
    background-color: var(--vscode-charts-yellow);
  }

  .status-dot.info {
    background-color: var(--vscode-charts-blue);
  }

  .status-dot.inactive {
    background-color: var(--vscode-descriptionForeground);
    opacity: 0.5;
  }

  /* Loading spinner */
  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid var(--vscode-panel-border);
    border-radius: 50%;
    border-top-color: var(--vscode-progressBar-background);
    animation: spin 1s ease-in-out infinite;
  }

  .spinner-large {
    width: 24px;
    height: 24px;
    border-width: 3px;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* Transitions */
  .transition {
    transition: all 0.15s ease-in-out;
  }

  .transition-colors {
    transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
  }

  .transition-opacity {
    transition: opacity 0.15s ease-in-out;
  }

  .transition-transform {
    transition: transform 0.15s ease-in-out;
  }
`;
    /**
     * All shared styles combined
     */
    const sharedStyles = i$3 `
  ${vscodeThemeVariables}
  ${layoutStyles}
  ${spacingStyles}
  ${typographyStyles}
  ${stateStyles}
  ${componentStyles}
`;

    /**
     * VS Code theme integration for AutoGen extension
     * Handles theme detection, switching, and provides theme-aware utilities
     */
    /**
     * Theme types supported by VS Code
     */
    var VSCodeTheme;
    (function (VSCodeTheme) {
        VSCodeTheme["DARK"] = "dark";
        VSCodeTheme["LIGHT"] = "light";
        VSCodeTheme["HIGH_CONTRAST_DARK"] = "hc-black";
        VSCodeTheme["HIGH_CONTRAST_LIGHT"] = "hc-light";
    })(VSCodeTheme || (VSCodeTheme = {}));
    /**
     * Theme detection utility
     */
    class ThemeManager {
        constructor() {
            this._currentTheme = VSCodeTheme.DARK;
            this._observers = new Set();
            this.detectTheme();
            this.setupThemeObserver();
        }
        static getInstance() {
            if (!this._instance) {
                this._instance = new ThemeManager();
            }
            return this._instance;
        }
        /**
         * Get current theme
         */
        get currentTheme() {
            return this._currentTheme;
        }
        /**
         * Check if current theme is dark
         */
        get isDark() {
            return this._currentTheme === VSCodeTheme.DARK ||
                this._currentTheme === VSCodeTheme.HIGH_CONTRAST_DARK;
        }
        /**
         * Check if current theme is light
         */
        get isLight() {
            return this._currentTheme === VSCodeTheme.LIGHT ||
                this._currentTheme === VSCodeTheme.HIGH_CONTRAST_LIGHT;
        }
        /**
         * Check if current theme is high contrast
         */
        get isHighContrast() {
            return this._currentTheme === VSCodeTheme.HIGH_CONTRAST_DARK ||
                this._currentTheme === VSCodeTheme.HIGH_CONTRAST_LIGHT;
        }
        /**
         * Detect current theme from body class or CSS variables
         */
        detectTheme() {
            // Check body classes first
            const body = document.body;
            if (body.classList.contains('vscode-dark')) {
                this._currentTheme = VSCodeTheme.DARK;
            }
            else if (body.classList.contains('vscode-light')) {
                this._currentTheme = VSCodeTheme.LIGHT;
            }
            else if (body.classList.contains('vscode-high-contrast')) {
                this._currentTheme = VSCodeTheme.HIGH_CONTRAST_DARK;
            }
            else if (body.classList.contains('vscode-high-contrast-light')) {
                this._currentTheme = VSCodeTheme.HIGH_CONTRAST_LIGHT;
            }
            else {
                // Fallback: detect from CSS variables
                const backgroundColor = getComputedStyle(document.documentElement)
                    .getPropertyValue('--vscode-editor-background').trim();
                if (backgroundColor) {
                    // Convert hex/rgb to determine if dark/light
                    const isLightBackground = this.isLightColor(backgroundColor);
                    this._currentTheme = isLightBackground ? VSCodeTheme.LIGHT : VSCodeTheme.DARK;
                }
            }
        }
        /**
         * Setup theme change observer
         */
        setupThemeObserver() {
            // Watch for changes in body class
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        const oldTheme = this._currentTheme;
                        this.detectTheme();
                        if (oldTheme !== this._currentTheme) {
                            this.notifyThemeChange();
                        }
                    }
                });
            });
            observer.observe(document.body, {
                attributes: true,
                attributeFilter: ['class']
            });
            // Also watch for CSS variable changes
            const style = document.documentElement;
            const styleObserver = new MutationObserver(() => {
                const oldTheme = this._currentTheme;
                this.detectTheme();
                if (oldTheme !== this._currentTheme) {
                    this.notifyThemeChange();
                }
            });
            styleObserver.observe(style, {
                attributes: true,
                attributeFilter: ['style']
            });
        }
        /**
         * Determine if a color is light or dark
         */
        isLightColor(color) {
            // Convert color to RGB values
            let r, g, b;
            if (color.startsWith('#')) {
                // Hex color
                const hex = color.slice(1);
                r = parseInt(hex.substr(0, 2), 16);
                g = parseInt(hex.substr(2, 2), 16);
                b = parseInt(hex.substr(4, 2), 16);
            }
            else if (color.startsWith('rgb')) {
                // RGB/RGBA color
                const values = color.match(/\d+/g);
                if (values && values.length >= 3) {
                    r = parseInt(values[0]);
                    g = parseInt(values[1]);
                    b = parseInt(values[2]);
                }
                else {
                    return false; // Default to dark if can't parse
                }
            }
            else {
                return false; // Default to dark for unknown formats
            }
            // Calculate luminance
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
            return luminance > 0.5;
        }
        /**
         * Subscribe to theme changes
         */
        subscribe(callback) {
            this._observers.add(callback);
            // Return unsubscribe function
            return () => {
                this._observers.delete(callback);
            };
        }
        /**
         * Notify all observers of theme change
         */
        notifyThemeChange() {
            this._observers.forEach(callback => {
                try {
                    callback(this._currentTheme);
                }
                catch (error) {
                    console.error('Error in theme change callback:', error);
                }
            });
        }
    }
    /**
     * Theme-specific CSS styles
     */
    const themeStyles = i$3 `
  /* Dark theme specific styles */
  :host(.theme-dark) {
    --autogen-shadow-light: rgba(0, 0, 0, 0.3);
    --autogen-shadow-medium: rgba(0, 0, 0, 0.5);
    --autogen-shadow-heavy: rgba(0, 0, 0, 0.7);
    --autogen-overlay: rgba(0, 0, 0, 0.5);
    --autogen-glass: rgba(255, 255, 255, 0.05);
  }

  /* Light theme specific styles */
  :host(.theme-light) {
    --autogen-shadow-light: rgba(0, 0, 0, 0.1);
    --autogen-shadow-medium: rgba(0, 0, 0, 0.15);
    --autogen-shadow-heavy: rgba(0, 0, 0, 0.25);
    --autogen-overlay: rgba(0, 0, 0, 0.3);
    --autogen-glass: rgba(0, 0, 0, 0.03);
  }

  /* High contrast theme specific styles */
  :host(.theme-high-contrast) {
    --autogen-shadow-light: rgba(0, 0, 0, 0.8);
    --autogen-shadow-medium: rgba(0, 0, 0, 0.9);
    --autogen-shadow-heavy: rgba(0, 0, 0, 1);
    --autogen-overlay: rgba(0, 0, 0, 0.8);
    --autogen-glass: transparent;
  }

  /* Common shadow utilities */
  .shadow-sm {
    box-shadow: 0 1px 2px var(--autogen-shadow-light);
  }

  .shadow-md {
    box-shadow: 0 2px 4px var(--autogen-shadow-medium);
  }

  .shadow-lg {
    box-shadow: 0 4px 8px var(--autogen-shadow-medium);
  }

  .shadow-xl {
    box-shadow: 0 8px 16px var(--autogen-shadow-heavy);
  }

  .shadow-inner {
    box-shadow: inset 0 1px 2px var(--autogen-shadow-light);
  }

  /* Glass effect */
  .glass {
    background-color: var(--autogen-glass);
    backdrop-filter: blur(8px);
    border: 1px solid var(--vscode-panel-border);
  }

  /* Overlay */
  .overlay {
    background-color: var(--autogen-overlay);
  }
`;
    /**
     * Theme-aware mixin for components
     */
    i$3 `
  ${themeStyles}

  /* Automatic theme class application based on VS Code theme */
  :host {
    /* Will be dynamically updated by ThemeManager */
  }
`;
    /**
     * Utility function to apply theme class to component
     */
    function applyThemeClass(element) {
        const themeManager = ThemeManager.getInstance();
        const updateThemeClass = (theme) => {
            // Remove existing theme classes
            element.classList.remove('theme-dark', 'theme-light', 'theme-high-contrast');
            // Add current theme class
            switch (theme) {
                case VSCodeTheme.DARK:
                    element.classList.add('theme-dark');
                    break;
                case VSCodeTheme.LIGHT:
                    element.classList.add('theme-light');
                    break;
                case VSCodeTheme.HIGH_CONTRAST_DARK:
                case VSCodeTheme.HIGH_CONTRAST_LIGHT:
                    element.classList.add('theme-high-contrast');
                    break;
            }
        };
        // Apply current theme
        updateThemeClass(themeManager.currentTheme);
        // Subscribe to theme changes
        const unsubscribe = themeManager.subscribe(updateThemeClass);
        // Return cleanup function
        return unsubscribe;
    }
    /**
     * Reactive theme property decorator for Lit components
     */
    function themeProperty() {
        return function (target, propertyKey) {
            const themeManager = ThemeManager.getInstance();
            // Define getter/setter
            Object.defineProperty(target, propertyKey, {
                get() {
                    return themeManager.currentTheme;
                },
                enumerable: true,
                configurable: true
            });
            // Setup theme change subscription in connectedCallback
            const originalConnectedCallback = target.connectedCallback;
            target.connectedCallback = function () {
                if (originalConnectedCallback) {
                    originalConnectedCallback.call(this);
                }
                // Subscribe to theme changes and trigger re-render
                this._themeUnsubscribe = themeManager.subscribe(() => {
                    this.requestUpdate(propertyKey);
                });
                // Apply theme class
                this._themeClassUnsubscribe = applyThemeClass(this);
            };
            // Cleanup in disconnectedCallback
            const originalDisconnectedCallback = target.disconnectedCallback;
            target.disconnectedCallback = function () {
                if (originalDisconnectedCallback) {
                    originalDisconnectedCallback.call(this);
                }
                if (this._themeUnsubscribe) {
                    this._themeUnsubscribe();
                }
                if (this._themeClassUnsubscribe) {
                    this._themeClassUnsubscribe();
                }
            };
        };
    }
    /**
     * Export theme manager instance for global use
     */
    ThemeManager.getInstance();

    /**
     * AutoGen Dashboard Component
     * Main dashboard interface built with Lit 3 - extends BasePanel
     */
    exports.AutoGenDashboard = class AutoGenDashboard extends BasePanel {
        static { this.styles = i$3 `
    ${sharedStyles}

    .status {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 16px;
    }

    .status-indicator {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background-color: var(--vscode-charts-red);
    }

    .status-indicator.connected {
      background-color: var(--vscode-charts-green);
    }

    .status-text {
      font-size: 14px;
      opacity: 0.8;
    }

    .dashboard-sections {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 24px;
    }

    .section {
      background-color: var(--vscode-input-background);
      border: 1px solid var(--vscode-panel-border);
      border-radius: 4px;
      padding: 20px;
    }

    .section-title {
      font-size: 16px;
      font-weight: 500;
      margin: 0 0 12px 0;
      color: var(--vscode-titleBar-activeForeground);
    }

    .placeholder {
      padding: 20px;
      text-align: center;
      border: 1px dashed var(--vscode-input-border);
      border-radius: 4px;
      opacity: 0.7;
      background-color: var(--vscode-editor-background);
    }

    .actions {
      display: flex;
      gap: 12px;
      margin-top: 24px;
      flex-wrap: wrap;
    }
  `; }
        constructor() {
            super();
            this.projectName = 'AutoGen Agile Project';
            this.connected = false;
            this.title = 'AutoGen Dashboard';
            this.subtitle = 'Multi-agent workflow management';
            this.refreshable = true;
        }
        renderContent() {
            return x `
      <div class="status">
        <div class="status-indicator \${this.connected ? 'connected' : ''}"></div>
        <span class="status-text">
          \${this.connected ? 'Connected to AutoGen MCP' : 'Disconnected from MCP Server'}
        </span>
      </div>

      <div class="dashboard-sections">
        <div class="section">
          <h3 class="section-title">Active Sessions</h3>
          <div class="placeholder">
            No active AutoGen sessions
          </div>
        </div>

        <div class="section">
          <h3 class="section-title">Recent Activities</h3>
          <div class="placeholder">
            Recent agent interactions will appear here
          </div>
        </div>

        <div class="section">
          <h3 class="section-title">Project Memory</h3>
          <div class="placeholder">
            Persistent project context and memory
          </div>
        </div>
      </div>

      <div class="actions">
        <button class="btn" @click="\${this._startNewSession}">
          Start New Session
        </button>
        <button class="btn secondary" @click="\${this._connectToMcp}">
          \${this.connected ? 'Reconnect' : 'Connect to MCP'}
        </button>
        <button class="btn secondary" @click="\${this._openSettings}">
          Settings
        </button>
      </div>
    `;
        }
        async onRefresh() {
            // Override with actual refresh logic
            await this.handleAsync(new Promise(resolve => setTimeout(resolve, 1000)), 'Failed to refresh dashboard');
        }
        _startNewSession() {
            this.dispatchCustomEvent('start-session', {
                projectName: this.projectName
            });
        }
        _connectToMcp() {
            this.dispatchCustomEvent('connect-mcp', {
                connected: this.connected
            });
        }
        _openSettings() {
            this.dispatchCustomEvent('open-settings');
        }
        connectedCallback() {
            super.connectedCallback();
            console.log('AutoGen Dashboard connected to DOM');
        }
    };
    __decorate([
        n({ type: String })
    ], exports.AutoGenDashboard.prototype, "projectName", void 0);
    __decorate([
        n({ type: Boolean })
    ], exports.AutoGenDashboard.prototype, "connected", void 0);
    __decorate([
        themeProperty()
    ], exports.AutoGenDashboard.prototype, "theme", void 0);
    exports.AutoGenDashboard = __decorate([
        t('autogen-dashboard')
    ], exports.AutoGenDashboard);

    return exports;

})({});
//# sourceMappingURL=dashboard.js.map
