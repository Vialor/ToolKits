# 打包方法：
# 根据这个命令的结果修改后续命令：python -c "import sys, pathlib; root=pathlib.Path(sys.executable).parent; hits=list(root.rglob('tcl*.*dll'))+list(root.rglob('tk*.*dll')); print('\n'.join(str(x) for x in hits[:50]))"
# 运行：
# pyinstaller --clean --noconfirm --onefile --windowed \
#   --add-data "$LOCALAPPDATA/Programs/Python/Python313/tcl;tcl" \
#   --add-binary "$LOCALAPPDATA/Programs/Python/Python313/DLLs/tcl86t.dll;." \
#   --add-binary "$LOCALAPPDATA/Programs/Python/Python313/DLLs/tk86t.dll;." \
#   formatter.py

from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import tkinter.messagebox as messagebox

import json
import ast
import pprint
import yaml
from json_repair import repair_json

class Application(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        
        self.__init__style()
        
        # 让 Application 铺满 root
        self.grid(row=0, column=0, sticky="nsew")
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # container 负责 padding（避免 root 背景露出来）
        self.container = ttk.Frame(self, padding=10)
        self.container.grid(row=0, column=0, sticky="nsew")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.container.rowconfigure(5, weight=1)
        self.container.columnconfigure(0, weight=1)
        
        self.statusVar = StringVar(value="Ready")
        
        self._createWidgets()
    
    def __init__style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Danger.TButton",
            foreground="white",
            background="#D32F2F",   # 红色
            padding=6
        )

        style.map(
            "Danger.TButton",
            background=[
                ("active", "#B71C1C"),   # 鼠标悬停/按下更深
            ]
        )
    
    def safe(self, fn, ok_status="Done"):
        """
        Wrap tk command callbacks with unified error handling.
        """
        def wrapped():
            try:
                fn()
                self.statusVar.set(ok_status)
            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.statusVar.set("Error")
        return wrapped
        
    def _bindStatusHint(self, widget, text):
        widget.bind("<Enter>", lambda e: self.statusVar.set(text), add="+")
        widget.bind("<Leave>", lambda e: self.statusVar.set("Ready"), add="+")

    def _createWidgets(self):
        # Input
        ttk.Label(self.container, text="Input").grid(row=0, column=0, sticky="w")
        self.textInput = ScrolledText(self.container, width=60, height=10, wrap="word")
        self.textInput.grid(row=1, column=0, sticky="nsew", pady=(4, 10))
        self.rowconfigure(1, weight=1)

        # Output
        ttk.Label(self.container, text="Output").grid(row=2, column=0, sticky="w")
        self.textOutput = ScrolledText(self.container, width=60, height=10, wrap="word")
        self.textOutput.grid(row=3, column=0, sticky="nsew", pady=(4, 10))
        self.rowconfigure(3, weight=1)
                
        # Buttons
        btnFrame = ttk.Frame(self.container)
        btnFrame.grid(row=4, column=0, sticky="ew", pady=(0, 2))

        for i in range(6):
            btnFrame.columnconfigure(i, weight=1)

        btnTextToJson = ttk.Button(
            btnFrame,
            text="text → json str",
            command=self.safe(self.textToJsonStr)
        )
        btnTextToJson.grid(row=0, column=0, sticky="ew", padx=4)
        self._bindStatusHint(
            btnTextToJson,
            "把普通文本转成 JSON 字符串（自动加引号并转义）"
        )

        btnStrToText = ttk.Button(
            btnFrame,
            text="str → text",
            command=self.safe(self.strToText)
        )
        btnStrToText.grid(row=0, column=1, sticky="ew", padx=4)
        self._bindStatusHint(
            btnStrToText,
            "解析字符串字面量到文本：支持 'abc' 或 \"abc\""
        )

        btnPyDictToJson = ttk.Button(
            btnFrame,
            text="python dict → json",
            command=self.safe(self.pyDictToJson)
        )
        btnPyDictToJson.grid(row=0, column=2, sticky="ew", padx=4)
        self._bindStatusHint(
            btnPyDictToJson,
            "把 Python dict 转成格式化 JSON（indent=2）"
        )


        btnJsonToPyDict = ttk.Button(
            btnFrame,
            text="json → python dict",
            command=self.safe(self.jsonToPyDict)
        )
        btnJsonToPyDict.grid(row=0, column=3, sticky="ew", padx=4)
        self._bindStatusHint(
            btnJsonToPyDict,
            "解析 JSON object 并按 Python dict 格式输出"
        )

        btnJsonToYaml = ttk.Button(
            btnFrame,
            text="json → yaml",
            command=self.safe(self.jsonToYaml)
        )
        btnJsonToYaml.grid(row=0, column=4, sticky="ew", padx=4)
        self._bindStatusHint(
            btnJsonToYaml,
            "把 JSON 转成 YAML（保留中文，不排序 key）"
        )

        btnYamlToJson = ttk.Button(
            btnFrame,
            text="yaml → json",
            command=self.safe(self.yamlToJson)
        )
        btnYamlToJson.grid(row=0, column=5, sticky="ew", padx=4)
        self._bindStatusHint(
            btnYamlToJson,
            "把 YAML 转成格式化 JSON（indent=2）"
        )

        btnRepairJson = ttk.Button(
            btnFrame,
            text="repair json format",
            command=self.safe(self.repairJson)
        )
        btnRepairJson.grid(row=1, column=0, sticky="ew", padx=4)
        self._bindStatusHint(
            btnRepairJson,
            "尝试修复不合法 JSON 并重新格式化"
        )
        
        btnPprint = ttk.Button(
            btnFrame,
            text="pprint",
            command=self.safe(self.pprint)
        )
        btnPprint.grid(row=1, column=1, sticky="ew", padx=4)
        self._bindStatusHint(
            btnPprint,
            "结构化美化输出，方便阅读复杂对象"
        )

        btnFormatByBrackets = ttk.Button(
            btnFrame,
            text="format by brackets",
            command=self.safe(self.formatByBrackets)
        )
        btnFormatByBrackets.grid(row=1, column=2, sticky="ew", padx=4)
        self._bindStatusHint(
            btnFormatByBrackets,
            "根据 [] {} () 自动缩进；忽略字符串内部括号；可处理未知格式的数据，甚至是括号缺失的情况。"
        )
                
        # Status Bar
        statusFrame = ttk.Frame(self.container)
        statusFrame.grid(row=5, column=0, sticky="ew", pady=(6, 0))
        statusFrame.columnconfigure(0, weight=1)

        statusLabel = ttk.Label(
            statusFrame,
            textvariable=self.statusVar,
            anchor="w"
        )
        statusLabel.grid(row=0, column=0, sticky="ew")

    def setOutput(self, text):
        self.textOutput.delete("1.0", END)
        self.textOutput.insert(END, text)
    
    def getInput(self) -> str:
        s = self.textInput.get("1.0", "end-1c").strip()
        if not s:
            raise ValueError("Empty input")
        return s
    
    def textToJsonStr(self):
        s = self.getInput()
        result =  json.dumps(s, ensure_ascii=False)
        self.setOutput(result)
    
    def strToText(self):
        s = self.getInput()
        result = ast.literal_eval(s)
        if not isinstance(result, str):
            raise ValueError("Input must be a quoted string literal, e.g. 'true' or \"true\"")
        self.setOutput(result)

    def pyDictToJson(self):
        s = self.getInput()
        d = ast.literal_eval(s)
        if not isinstance(d, dict):
            raise ValueError("Input is not a dict")

        result = json.dumps(d, ensure_ascii=False, indent=2)
        self.setOutput(result)
            
    def jsonToPyDict(self):
        s = self.getInput()
        # 解析 JSON
        obj = json.loads(s)

        # 必须是 dict
        if not isinstance(obj, dict):
            raise ValueError("JSON is not an object (dict)")

        # 输出 Python dict 格式
        result = pprint.pformat(
            obj,
            indent=2,
            width=100,
            sort_dicts=False
        )

        self.setOutput(result)
            
    def jsonToYaml(self):
        s = self.getInput()
        obj = json.loads(s)  # JSON -> Python
        # YAML 输出：保持 unicode、尽量不折行、不要排序 key
        result = yaml.safe_dump(
            obj,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=100000  # 防止长字符串被自动换行
        )
        self.setOutput(result.strip())

    def yamlToJson(self):
        s = self.getInput()
        obj = yaml.safe_load(s)  # YAML -> Python
        # YAML 可能是空内容/空文档
        if obj is None:
            raise ValueError("YAML is empty or parsed to None")
        result = json.dumps(obj, ensure_ascii=False, indent=2)
        self.setOutput(result)
    
    def repairJson(self):
        s = self.getInput()
        repaired = repair_json(s)
        # 再解析一次，确保是合法 JSON
        obj = json.loads(repaired)
        # 格式化输出
        result = json.dumps(obj, ensure_ascii=False, indent=2)
        self.setOutput(result)
            
    def pprint(self):
        s = self.getInput()
        # 优先按 JSON 解析
        try:
            obj = json.loads(s)
        except Exception:
            # JSON 失败再尝试 Python literal
            obj = ast.literal_eval(s)

        # pprint 美化输出
        result = pprint.pformat(
            obj,
            indent=2,
            width=100,
            compact=False,
            sort_dicts=False
        )

        self.setOutput(result)

    
    
    def formatByBrackets(self, indent=2):
        text = self.getInput()
        opens = "([{"
        closes = ")]}"
        match_close_to_open = {')': '(', ']': '[', '}': '{'}

        out = []
        stack = []  # store opening brackets
        level = 0

        in_str = False
        str_quote = ""   # "'" or '"'
        escape = False

        def write(s: str):
            out.append(s)

        def newline():
            # avoid duplicate blank lines / trailing spaces
            # remove trailing spaces
            while out and out[-1].endswith(" ") and out[-1].strip() == "":
                out.pop()
            write("\n" + (" " * (level * indent)))

        def last_nonspace_char():
            for chunk in reversed(out):
                for ch in reversed(chunk):
                    if not ch.isspace():
                        return ch
            return ""

        i = 0
        n = len(text)

        while i < n:
            ch = text[i]

            if in_str:
                write(ch)
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == str_quote:
                    in_str = False
                    str_quote = ""
                i += 1
                continue

            # not in string:
            if ch in ("'", '"'):
                in_str = True
                str_quote = ch
                write(ch)
                i += 1
                continue

            if ch in opens:
                # write the opening bracket
                write(ch)
                stack.append(ch)
                level += 1

                # if next non-space is a closing bracket, keep inline: "()"
                j = i + 1
                while j < n and text[j].isspace():
                    j += 1
                if j < n and text[j] in closes:
                    # do nothing
                    pass
                else:
                    newline()
                i += 1
                continue

            if ch in closes:
                # pop if matches; if not, still try to decrease level safely
                expected_open = match_close_to_open.get(ch)
                if stack and stack[-1] == expected_open:
                    stack.pop()
                    level = max(0, level - 1)
                else:
                    # unmatched close: best-effort decrease but don't go negative
                    level = max(0, level - 1)

                # move closing bracket to its own aligned line if previous char isn't an opening bracket
                prev = last_nonspace_char()
                if prev and prev not in opens and prev != "\n":
                    newline()

                write(ch)

                # if next char is a comma, keep on same line (",")
                j = i + 1
                while j < n and text[j].isspace():
                    j += 1
                if j < n and text[j] == ",":
                    pass
                else:
                    # otherwise, if more content follows, newline
                    if j < n:
                        newline()
                i += 1
                continue

            if ch == ",":
                write(ch)
                # comma splits items (outside strings)
                newline()
                i += 1
                continue

            # collapse excessive whitespace outside strings (optional but usually nicer)
            if ch.isspace():
                # keep a single space if between tokens on same line
                prev = last_nonspace_char()
                if prev and prev not in "\n" and prev not in opens and prev not in ",":
                    # lookahead: don't insert space before punctuation
                    j = i + 1
                    while j < n and text[j].isspace():
                        j += 1
                    if j < n and text[j] not in closes and text[j] != ",":
                        write(" ")
                i += 1
                continue

            write(ch)
            i += 1

        # cleanup: strip trailing whitespace per line
        formatted = "".join(out)
        formatted = "\n".join(line.rstrip() for line in formatted.splitlines()).strip()
        self.setOutput(formatted)
    

if __name__ == "__main__":
    root = Tk()
    root.title("Format Converter")
    root.minsize(720, 520)
    
    app = Application(master=root)
    app.mainloop()
