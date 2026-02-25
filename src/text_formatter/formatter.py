# 打包方法：
# 根据这个命令修改后续命令：python -c "import sys, pathlib; root=pathlib.Path(sys.executable).parent; hits=list(root.rglob('tcl*.*dll'))+list(root.rglob('tk*.*dll')); print('\n'.join(str(x) for x in hits[:50]))"
# 运行：
# pyinstaller --clean --noconfirm --onefile --windowed \
#   --add-data "$LOCALAPPDATA/Programs/Python/Python313/tcl;tcl" \
#   --add-binary "$LOCALAPPDATA/Programs/Python/Python313/DLLs/tcl86t.dll;." \
#   --add-binary "$LOCALAPPDATA/Programs/Python/Python313/DLLs/tk86t.dll;." \
#   text_formatter.py

from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import tkinter.messagebox as messagebox

import json
import ast
import pprint
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
        self.container.rowconfigure(1, weight=1)
        self.container.rowconfigure(3, weight=1)
        self.container.columnconfigure(0, weight=1)
        
        self._create_widgets()
    
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

    def _create_widgets(self):
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

        for i in range(4):
            btnFrame.columnconfigure(i, weight=1)

        ttk.Button(btnFrame,
            text="text → json str",
            command=self.textToJsonStr
        ).grid(row=0, column=0, sticky="ew", padx=4)

        ttk.Button(btnFrame,
            text="json str → text",
            command=self.jsonStrToText
        ).grid(row=0, column=1, sticky="ew", padx=4)

        ttk.Button(btnFrame,
            text="python dict → json",
            command=self.pyDictToJson
        ).grid(row=0, column=2, sticky="ew", padx=4)
        
        ttk.Button(btnFrame,
            text="json → python dict",
            command=self.jsonToPyDict
        ).grid(row=0, column=3, sticky="ew", padx=4)
        
        ttk.Button(btnFrame,
            text="repair json format",
            command=self.repairJson
        ).grid(row=1, column=0, sticky="ew", padx=4)
        
        ttk.Button(btnFrame,
            text="pprint",
            command=self.pprint
        ).grid(row=1, column=1, sticky="ew", padx=4)
        
        ttk.Button(
            btnFrame,
            text="Quit",
            style="Danger.TButton",
            command=self.quit
        ).grid(
            row=2,
            column=3,
            columnspan=1,
            sticky="ew",
            padx=4,
            pady=(8, 0)
        )

    def setOutput(self, text):
        self.textOutput.delete("1.0", END)
        self.textOutput.insert(END, text)
    
    def getInput(self) -> str:
        return self.textInput.get("1.0", "end-1c")
    
    def textToJsonStr(self):
        s = self.getInput()
        result =  json.dumps(s, ensure_ascii=False)
        self.setOutput(result)
    
    def jsonStrToText(self):
        s = self.getInput()
        try:
            result = json.loads(s)
            self.setOutput(result)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def pyDictToJson(self):
        s = self.getInput().strip()
        try:
            if not s:
                raise ValueError("Empty input")
            d = ast.literal_eval(s)
            if not isinstance(d, dict):
                raise ValueError("Input is not a dict")

            result = json.dumps(d, ensure_ascii=False, indent=2)
            self.setOutput(result)

        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def repairJson(self):
        s = self.getInput()
        try:
            repaired = repair_json(s)
            # 再解析一次，确保是合法 JSON
            obj = json.loads(repaired)
            # 格式化输出
            result = json.dumps(obj, ensure_ascii=False, indent=2)
            self.setOutput(result)

        except Exception as e:
            messagebox.showerror("Error", str(e))
            
    def pprint(self):
        s = self.getInput().strip()
        try:
            if not s:
                raise ValueError("Empty input")

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

        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def jsonToPyDict(self):
        s = self.getInput().strip()
        try:
            if not s:
                raise ValueError("Empty input")

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

        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = Tk()
    root.title("Format Converter")
    root.minsize(720, 520)
    
    app = Application(master=root)
    app.mainloop()
