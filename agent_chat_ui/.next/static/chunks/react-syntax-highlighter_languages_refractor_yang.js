"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
(self["webpackChunk_N_E"] = self["webpackChunk_N_E"] || []).push([["react-syntax-highlighter_languages_refractor_yang"],{

/***/ "(app-pages-browser)/./node_modules/.pnpm/refractor@3.6.0/node_modules/refractor/lang/yang.js":
/*!********************************************************************************!*\
  !*** ./node_modules/.pnpm/refractor@3.6.0/node_modules/refractor/lang/yang.js ***!
  \********************************************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

eval(__webpack_require__.ts("\n\nmodule.exports = yang\nyang.displayName = 'yang'\nyang.aliases = []\nfunction yang(Prism) {\n  Prism.languages.yang = {\n    // https://tools.ietf.org/html/rfc6020#page-34\n    // http://www.yang-central.org/twiki/bin/view/Main/YangExamples\n    comment: /\\/\\*[\\s\\S]*?\\*\\/|\\/\\/.*/,\n    string: {\n      pattern: /\"(?:[^\\\\\"]|\\\\.)*\"|'[^']*'/,\n      greedy: true\n    },\n    keyword: {\n      pattern: /(^|[{};\\r\\n][ \\t]*)[a-z_][\\w.-]*/i,\n      lookbehind: true\n    },\n    namespace: {\n      pattern: /(\\s)[a-z_][\\w.-]*(?=:)/i,\n      lookbehind: true\n    },\n    boolean: /\\b(?:false|true)\\b/,\n    operator: /\\+/,\n    punctuation: /[{};:]/\n  }\n}\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKGFwcC1wYWdlcy1icm93c2VyKS8uL25vZGVfbW9kdWxlcy8ucG5wbS9yZWZyYWN0b3JAMy42LjAvbm9kZV9tb2R1bGVzL3JlZnJhY3Rvci9sYW5nL3lhbmcuanMiLCJtYXBwaW5ncyI6IkFBQVk7O0FBRVo7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUNBLHVCQUF1QjtBQUN2QjtBQUNBLEtBQUs7QUFDTDtBQUNBO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDQTtBQUNBLHNCQUFzQjtBQUN0QjtBQUNBIiwic291cmNlcyI6WyIvVXNlcnMvYnl0ZWRhbmNlL1B5Y2hhcm1Qcm9qZWN0cy9teV9iZXN0L2xhbmdncmFwaF90ZWFjaC9hZ2VudF9jaGF0X3VpL25vZGVfbW9kdWxlcy8ucG5wbS9yZWZyYWN0b3JAMy42LjAvbm9kZV9tb2R1bGVzL3JlZnJhY3Rvci9sYW5nL3lhbmcuanMiXSwic291cmNlc0NvbnRlbnQiOlsiJ3VzZSBzdHJpY3QnXG5cbm1vZHVsZS5leHBvcnRzID0geWFuZ1xueWFuZy5kaXNwbGF5TmFtZSA9ICd5YW5nJ1xueWFuZy5hbGlhc2VzID0gW11cbmZ1bmN0aW9uIHlhbmcoUHJpc20pIHtcbiAgUHJpc20ubGFuZ3VhZ2VzLnlhbmcgPSB7XG4gICAgLy8gaHR0cHM6Ly90b29scy5pZXRmLm9yZy9odG1sL3JmYzYwMjAjcGFnZS0zNFxuICAgIC8vIGh0dHA6Ly93d3cueWFuZy1jZW50cmFsLm9yZy90d2lraS9iaW4vdmlldy9NYWluL1lhbmdFeGFtcGxlc1xuICAgIGNvbW1lbnQ6IC9cXC9cXCpbXFxzXFxTXSo/XFwqXFwvfFxcL1xcLy4qLyxcbiAgICBzdHJpbmc6IHtcbiAgICAgIHBhdHRlcm46IC9cIig/OlteXFxcXFwiXXxcXFxcLikqXCJ8J1teJ10qJy8sXG4gICAgICBncmVlZHk6IHRydWVcbiAgICB9LFxuICAgIGtleXdvcmQ6IHtcbiAgICAgIHBhdHRlcm46IC8oXnxbe307XFxyXFxuXVsgXFx0XSopW2Etel9dW1xcdy4tXSovaSxcbiAgICAgIGxvb2tiZWhpbmQ6IHRydWVcbiAgICB9LFxuICAgIG5hbWVzcGFjZToge1xuICAgICAgcGF0dGVybjogLyhcXHMpW2Etel9dW1xcdy4tXSooPz06KS9pLFxuICAgICAgbG9va2JlaGluZDogdHJ1ZVxuICAgIH0sXG4gICAgYm9vbGVhbjogL1xcYig/OmZhbHNlfHRydWUpXFxiLyxcbiAgICBvcGVyYXRvcjogL1xcKy8sXG4gICAgcHVuY3R1YXRpb246IC9be307Ol0vXG4gIH1cbn1cbiJdLCJuYW1lcyI6W10sImlnbm9yZUxpc3QiOlswXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///(app-pages-browser)/./node_modules/.pnpm/refractor@3.6.0/node_modules/refractor/lang/yang.js\n"));

/***/ })

}]);