"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
(self["webpackChunk_N_E"] = self["webpackChunk_N_E"] || []).push([["react-syntax-highlighter_languages_refractor_prolog"],{

/***/ "(app-pages-browser)/./node_modules/.pnpm/refractor@3.6.0/node_modules/refractor/lang/prolog.js":
/*!**********************************************************************************!*\
  !*** ./node_modules/.pnpm/refractor@3.6.0/node_modules/refractor/lang/prolog.js ***!
  \**********************************************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

eval(__webpack_require__.ts("\n\nmodule.exports = prolog\nprolog.displayName = 'prolog'\nprolog.aliases = []\nfunction prolog(Prism) {\n  Prism.languages.prolog = {\n    // Syntax depends on the implementation\n    comment: {\n      pattern: /\\/\\*[\\s\\S]*?\\*\\/|%.*/,\n      greedy: true\n    },\n    // Depending on the implementation, strings may allow escaped newlines and quote-escape\n    string: {\n      pattern: /([\"'])(?:\\1\\1|\\\\(?:\\r\\n|[\\s\\S])|(?!\\1)[^\\\\\\r\\n])*\\1(?!\\1)/,\n      greedy: true\n    },\n    builtin: /\\b(?:fx|fy|xf[xy]?|yfx?)\\b/,\n    // FIXME: Should we list all null-ary predicates (not followed by a parenthesis) like halt, trace, etc.?\n    function: /\\b[a-z]\\w*(?:(?=\\()|\\/\\d+)/,\n    number: /\\b\\d+(?:\\.\\d*)?/,\n    // Custom operators are allowed\n    operator: /[:\\\\=><\\-?*@\\/;+^|!$.]+|\\b(?:is|mod|not|xor)\\b/,\n    punctuation: /[(){}\\[\\],]/\n  }\n}\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKGFwcC1wYWdlcy1icm93c2VyKS8uL25vZGVfbW9kdWxlcy8ucG5wbS9yZWZyYWN0b3JAMy42LjAvbm9kZV9tb2R1bGVzL3JlZnJhY3Rvci9sYW5nL3Byb2xvZy5qcyIsIm1hcHBpbmdzIjoiQUFBWTs7QUFFWjtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDQTtBQUNBO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLDhCQUE4QjtBQUM5Qix1QkFBdUI7QUFDdkI7QUFDQSIsInNvdXJjZXMiOlsiL1VzZXJzL2J5dGVkYW5jZS9QeWNoYXJtUHJvamVjdHMvbXlfYmVzdC9sYW5nZ3JhcGhfdGVhY2gvYWdlbnRfY2hhdF91aS9ub2RlX21vZHVsZXMvLnBucG0vcmVmcmFjdG9yQDMuNi4wL25vZGVfbW9kdWxlcy9yZWZyYWN0b3IvbGFuZy9wcm9sb2cuanMiXSwic291cmNlc0NvbnRlbnQiOlsiJ3VzZSBzdHJpY3QnXG5cbm1vZHVsZS5leHBvcnRzID0gcHJvbG9nXG5wcm9sb2cuZGlzcGxheU5hbWUgPSAncHJvbG9nJ1xucHJvbG9nLmFsaWFzZXMgPSBbXVxuZnVuY3Rpb24gcHJvbG9nKFByaXNtKSB7XG4gIFByaXNtLmxhbmd1YWdlcy5wcm9sb2cgPSB7XG4gICAgLy8gU3ludGF4IGRlcGVuZHMgb24gdGhlIGltcGxlbWVudGF0aW9uXG4gICAgY29tbWVudDoge1xuICAgICAgcGF0dGVybjogL1xcL1xcKltcXHNcXFNdKj9cXCpcXC98JS4qLyxcbiAgICAgIGdyZWVkeTogdHJ1ZVxuICAgIH0sXG4gICAgLy8gRGVwZW5kaW5nIG9uIHRoZSBpbXBsZW1lbnRhdGlvbiwgc3RyaW5ncyBtYXkgYWxsb3cgZXNjYXBlZCBuZXdsaW5lcyBhbmQgcXVvdGUtZXNjYXBlXG4gICAgc3RyaW5nOiB7XG4gICAgICBwYXR0ZXJuOiAvKFtcIiddKSg/OlxcMVxcMXxcXFxcKD86XFxyXFxufFtcXHNcXFNdKXwoPyFcXDEpW15cXFxcXFxyXFxuXSkqXFwxKD8hXFwxKS8sXG4gICAgICBncmVlZHk6IHRydWVcbiAgICB9LFxuICAgIGJ1aWx0aW46IC9cXGIoPzpmeHxmeXx4Zlt4eV0/fHlmeD8pXFxiLyxcbiAgICAvLyBGSVhNRTogU2hvdWxkIHdlIGxpc3QgYWxsIG51bGwtYXJ5IHByZWRpY2F0ZXMgKG5vdCBmb2xsb3dlZCBieSBhIHBhcmVudGhlc2lzKSBsaWtlIGhhbHQsIHRyYWNlLCBldGMuP1xuICAgIGZ1bmN0aW9uOiAvXFxiW2Etel1cXHcqKD86KD89XFwoKXxcXC9cXGQrKS8sXG4gICAgbnVtYmVyOiAvXFxiXFxkKyg/OlxcLlxcZCopPy8sXG4gICAgLy8gQ3VzdG9tIG9wZXJhdG9ycyBhcmUgYWxsb3dlZFxuICAgIG9wZXJhdG9yOiAvWzpcXFxcPT48XFwtPypAXFwvOytefCEkLl0rfFxcYig/OmlzfG1vZHxub3R8eG9yKVxcYi8sXG4gICAgcHVuY3R1YXRpb246IC9bKCl7fVxcW1xcXSxdL1xuICB9XG59XG4iXSwibmFtZXMiOltdLCJpZ25vcmVMaXN0IjpbMF0sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(app-pages-browser)/./node_modules/.pnpm/refractor@3.6.0/node_modules/refractor/lang/prolog.js\n"));

/***/ })

}]);