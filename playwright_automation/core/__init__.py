# Playwright Automation Framework - Core Module
from .browser import BrowserManager, browser_manager
from .page import BasePage, PageManager
from .element import ElementHandler

__all__ = ['BrowserManager', 'browser_manager', 'BasePage', 'PageManager', 'ElementHandler']
