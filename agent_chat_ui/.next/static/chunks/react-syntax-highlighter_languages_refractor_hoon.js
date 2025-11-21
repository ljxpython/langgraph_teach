"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
(self["webpackChunk_N_E"] = self["webpackChunk_N_E"] || []).push([["react-syntax-highlighter_languages_refractor_hoon"],{

/***/ "(app-pages-browser)/./node_modules/.pnpm/refractor@3.6.0/node_modules/refractor/lang/hoon.js":
/*!********************************************************************************!*\
  !*** ./node_modules/.pnpm/refractor@3.6.0/node_modules/refractor/lang/hoon.js ***!
  \********************************************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

eval(__webpack_require__.ts("\n\nmodule.exports = hoon\nhoon.displayName = 'hoon'\nhoon.aliases = []\nfunction hoon(Prism) {\n  Prism.languages.hoon = {\n    comment: {\n      pattern: /::.*/,\n      greedy: true\n    },\n    string: {\n      pattern: /\"[^\"]*\"|'[^']*'/,\n      greedy: true\n    },\n    constant: /%(?:\\.[ny]|[\\w-]+)/,\n    'class-name': /@(?:[a-z0-9-]*[a-z0-9])?|\\*/i,\n    function: /(?:\\+[-+] {2})?(?:[a-z](?:[a-z0-9-]*[a-z0-9])?)/,\n    keyword:\n      /\\.[\\^\\+\\*=\\?]|![><:\\.=\\?!]|=[>|:,\\.\\-\\^<+;/~\\*\\?]|\\?[>|:\\.\\-\\^<\\+&~=@!]|\\|[\\$_%:\\.\\-\\^~\\*=@\\?]|\\+[|\\$\\+\\*]|:[_\\-\\^\\+~\\*]|%[_:\\.\\-\\^\\+~\\*=]|\\^[|:\\.\\-\\+&~\\*=\\?]|\\$[|_%:<>\\-\\^&~@=\\?]|;[:<\\+;\\/~\\*=]|~[>|\\$_%<\\+\\/&=\\?!]|--|==/\n  }\n}\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKGFwcC1wYWdlcy1icm93c2VyKS8uL25vZGVfbW9kdWxlcy8ucG5wbS9yZWZyYWN0b3JAMy42LjAvbm9kZV9tb2R1bGVzL3JlZnJhY3Rvci9sYW5nL2hvb24uanMiLCJtYXBwaW5ncyI6IkFBQVk7O0FBRVo7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUNBO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDQTtBQUNBLDBCQUEwQixFQUFFO0FBQzVCO0FBQ0EsaURBQWlELDJJQUEySSxNQUFNO0FBQ2xNO0FBQ0EiLCJzb3VyY2VzIjpbIi9Vc2Vycy9ieXRlZGFuY2UvUHljaGFybVByb2plY3RzL215X2Jlc3QvbGFuZ2dyYXBoX3RlYWNoL2FnZW50X2NoYXRfdWkvbm9kZV9tb2R1bGVzLy5wbnBtL3JlZnJhY3RvckAzLjYuMC9ub2RlX21vZHVsZXMvcmVmcmFjdG9yL2xhbmcvaG9vbi5qcyJdLCJzb3VyY2VzQ29udGVudCI6WyIndXNlIHN0cmljdCdcblxubW9kdWxlLmV4cG9ydHMgPSBob29uXG5ob29uLmRpc3BsYXlOYW1lID0gJ2hvb24nXG5ob29uLmFsaWFzZXMgPSBbXVxuZnVuY3Rpb24gaG9vbihQcmlzbSkge1xuICBQcmlzbS5sYW5ndWFnZXMuaG9vbiA9IHtcbiAgICBjb21tZW50OiB7XG4gICAgICBwYXR0ZXJuOiAvOjouKi8sXG4gICAgICBncmVlZHk6IHRydWVcbiAgICB9LFxuICAgIHN0cmluZzoge1xuICAgICAgcGF0dGVybjogL1wiW15cIl0qXCJ8J1teJ10qJy8sXG4gICAgICBncmVlZHk6IHRydWVcbiAgICB9LFxuICAgIGNvbnN0YW50OiAvJSg/OlxcLltueV18W1xcdy1dKykvLFxuICAgICdjbGFzcy1uYW1lJzogL0AoPzpbYS16MC05LV0qW2EtejAtOV0pP3xcXCovaSxcbiAgICBmdW5jdGlvbjogLyg/OlxcK1stK10gezJ9KT8oPzpbYS16XSg/OlthLXowLTktXSpbYS16MC05XSk/KS8sXG4gICAga2V5d29yZDpcbiAgICAgIC9cXC5bXFxeXFwrXFwqPVxcP118IVs+PDpcXC49XFw/IV18PVs+fDosXFwuXFwtXFxePCs7L35cXCpcXD9dfFxcP1s+fDpcXC5cXC1cXF48XFwrJn49QCFdfFxcfFtcXCRfJTpcXC5cXC1cXF5+XFwqPUBcXD9dfFxcK1t8XFwkXFwrXFwqXXw6W19cXC1cXF5cXCt+XFwqXXwlW186XFwuXFwtXFxeXFwrflxcKj1dfFxcXlt8OlxcLlxcLVxcKyZ+XFwqPVxcP118XFwkW3xfJTo8PlxcLVxcXiZ+QD1cXD9dfDtbOjxcXCs7XFwvflxcKj1dfH5bPnxcXCRfJTxcXCtcXC8mPVxcPyFdfC0tfD09L1xuICB9XG59XG4iXSwibmFtZXMiOltdLCJpZ25vcmVMaXN0IjpbMF0sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(app-pages-browser)/./node_modules/.pnpm/refractor@3.6.0/node_modules/refractor/lang/hoon.js\n"));

/***/ })

}]);