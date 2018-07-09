import sublime
import sublime_plugin
import functools
import os
import datetime
import json
import re
import subprocess
import sys
import time
import codecs

try:
    import helper
    import rebuild
    import definition
except ImportError:
    from . import helper
    from . import rebuild
    from . import definition

TEMP_PATH = ""
# [wordsArr,showFunc,path,lineNum,type] type=0 user, 1 lua, 2 cocos2dx
DEFINITION_LIST = []
USER_DEFINITION_LIST = []

def getExePath():
    settings = helper.loadSettings("Legend")
    ret = settings.get("legend_path", "")
    if len(ret) == 0:
        sublime.error_message("EXE path is not set!")
        return False
    return ret

def getStoragePath():
    settings = helper.loadSettings("Legend")
    ret = settings.get("storage_path", "")
    if len(ret) == 0:
        sublime.error_message("Storage path is not set!")
        return False
    return ret

def init():
    global TEMP_PATH
    TEMP_PATH = sublime.packages_path() + os.sep + "User" + os.sep + "QuickXDev.cache"
    global DEFINITION_LIST
    DEFINITION_LIST = json.loads(definition.data)
    global USER_DEFINITION_LIST
    path = os.path.join(TEMP_PATH, "user_definition.json")
    if os.path.exists(path):
        USER_DEFINITION_LIST = json.loads(helper.readFile(path))

process=None
def runWithPlayer(srcDir):
    global process

    args = [getExePath()]
    args.append("-workdir")
    args.append(srcDir + os.sep + "app")
    args.append("-writable-path")
    # args.append(srcDir + os.sep + "../../storage")
    args.append(getStoragePath())
    # if process:
    #     try:
    #         process.terminate()
    #     except Exception:
    #         pass
    if sublime.platform() == "osx":
        process = subprocess.Popen(args)
    elif sublime.platform() == "windows":
        process = subprocess.Popen(args)

class LegendWindowCommand(sublime_plugin.WindowCommand):
    def __init__(self, window):
        super(LegendWindowCommand, self).__init__(window)

    def run(self, dirs):
        runWithPlayer(dirs[0])

    def is_enabled(self, dirs):
        if len(dirs) != 1:
            return False
        mainLuaPath = dirs[0] + os.sep + "main.lua"
        if not os.path.exists(mainLuaPath):
            return False
        return True

    def is_visible(self, dirs):
        return self.is_enabled(dirs)

class LegendTextCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        path = self.view.file_name()
        sublime.status_message(path)
        index = path.rfind("src" + os.sep)
        if index == -1:
            sublime.status_message("This file is not in the 'src' folder!")
            return
        path = path[0 : index] + "src"
        runWithPlayer(path)

    def is_enabled(self):
        return helper.checkFileExt(self.view.file_name(), "lua")

    def is_visible(self):
        return self.is_enabled()

class LegendListener(sublime_plugin.EventListener):
    def __init__(self):
        self.lastTime = 0

    def on_post_save(self, view):
        filename = view.file_name()
        if not filename:
            return
        if not helper.checkFileExt(filename, "lua"):
            return
        #rebuild user definition
        curTime = time.time()
        if curTime - self.lastTime < 2:
            return
        self.lastTime = curTime
        a = rebuild.rebuildSingle(filename, TEMP_PATH)
        arr = a[0]
        path = a[1]
        # remove prev
        global USER_DEFINITION_LIST
        for i in range(len(USER_DEFINITION_LIST) - 1, 0, -1):
            item = USER_DEFINITION_LIST[i]
            if item[2] == path:
                USER_DEFINITION_LIST.remove(item)
        USER_DEFINITION_LIST.extend(arr)
        path = os.path.join(TEMP_PATH, "user_definition.json")
        data = json.dumps(USER_DEFINITION_LIST)
        if not os.path.exists(TEMP_PATH):
            os.makedirs(TEMP_PATH)
        helper.writeFile(path, data)
        sublime.status_message("Current file definition rebuild complete!")

def plugin_loaded():
    sublime.set_timeout(init, 200)
