"""
Compatibility shim: some raganything builds import MineruParser from lightrag.mineru_parser.

The actual implementation lives in raganything.parser, so we re-export it here to avoid
import errors when running local MCP services against the editable source tree.
"""

from raganything.parser import MineruParser

__all__ = ["MineruParser"]
