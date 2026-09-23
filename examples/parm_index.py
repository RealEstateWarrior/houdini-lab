# -*- coding: utf-8 -*-
"""実践の各段で使ったノードのつまみを、hip から取り出して out/parm_index.json に書く。

本文の太字（<strong>Pin Points に top</strong> など）に「どのタブのどこにあるか」を出すための表。
名前・置き場所・値はどれも hip の実物から取る（思い込みで書かない）。

    hython examples/parm_index.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out")


def find_node(name):
    import hou
    for top in hou.node("/obj").children():
        hit = top.node(name) if top.node(name) else None
        if hit is not None:
            return hit
        for child in top.allSubChildren():
            if child.name() == name:
                return child
    for net in ("/mat", "/out"):
        root = hou.node(net)
        if root is not None and root.node(name) is not None:
            return root.node(name)
    return None


def main():
    import hou
    with open(os.path.join(HERE, "guides.json"), encoding="utf-8") as fp:
        guides = json.load(fp)["guides"]
    index = {}
    for guide in guides:
        hip = os.path.join(OUT, guide.get("hip") or "")
        if not guide.get("hip") or not os.path.exists(hip):
            continue
        try:
            hou.hipFile.load(hip, suppress_save_prompt=True, ignore_load_warnings=True)
        except hou.OperationFailed:
            continue
        steps = {}
        for number, step in enumerate(guide["steps"], start=1):
            node = find_node(step.get("ui_node", ""))
            if node is None:
                continue
            parms = {}
            for parm in node.parms():
                template = parm.parmTemplate()
                if template.type() in (hou.parmTemplateType.Folder, hou.parmTemplateType.FolderSet,
                                       hou.parmTemplateType.Separator, hou.parmTemplateType.Label):
                    continue
                if parm.isHidden():
                    continue
                label = template.label().strip()
                tuple_ = parm.tuple()
                if len(tuple_) > 1:
                    label = tuple_.parmTemplate().label().strip()
                if len(label) < 2 or label in parms:
                    continue
                try:
                    if len(tuple_) > 1:
                        value = ", ".join(p.evalAsString() for p in tuple_)
                    else:
                        value = parm.evalAsString()
                except hou.Error:
                    value = ""
                folders = [f for f in parm.containingFolders() if f]
                parms[label] = [tuple_.name() if len(tuple_) > 1 else parm.name(),
                                " › ".join(folders), value[:60],
                                parm.isAtDefault()]
            steps[str(number)] = {"node": node.type().name().split("::")[0],
                                  "name": node.name(), "parms": parms}
        index[guide["id"]] = steps
        print(guide["id"], len(steps))
    with open(os.path.join(OUT, "parm_index.json"), "w", encoding="utf-8") as fp:
        json.dump(index, fp, ensure_ascii=False)
    print("実践", len(index), "本")


if __name__ == "__main__":
    main()
