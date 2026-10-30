# -*- coding: utf-8 -*-
"""给 public/index.html 打上移动端缩放适配补丁。

幂等：重复运行不会重复插入，已存在就跳过。
用途：当你拿到一份全新写好的 index.html（不含适配代码）时，跑一次即可。

用法:  python mobile_fix.py
"""
import io, os, re, sys

TARGET = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "public", "index.html")

MEDIA = """/* 手机窄屏：两列统计卡片，压缩留白 */
@media(max-width:520px){
  header{padding:12px 4%}
  .logo{font-size:17px}
  .hero{margin-top:20px;padding:0 4%}
  .hero h1{font-size:23px}
  .hero p{font-size:13px;margin-bottom:16px}
  .searchbox input{padding:12px 14px;font-size:14px}
  .searchbox button{padding:0 20px;font-size:15px}
  .stats{grid-template-columns:repeat(2,1fr);gap:10px}
  .stat{padding:14px 10px}
  .stat b{font-size:22px}
  .stat span{font-size:12px}
  .layout{padding:0 4%}
}
"""

SCRIPT = """<script>
/* 移动端缩放自适应：缩小页面时按视觉视口重新铺满，避免内容挤在左半边 */
(function () {
  var vv = window.visualViewport;
  if (!vv) return;
  var root = document.documentElement;
  var raf = null, lastW = 0, lastMode = null;
  function apply() {
    raf = null;
    var w = Math.round(vv.width || 0);
    if (!w) return;
    var zoomedOut = (vv.scale || 1) < 0.98;
    if (w === lastW && zoomedOut === lastMode) return;
    lastW = w; lastMode = zoomedOut;
    root.style.width = zoomedOut ? w + "px" : "";
    document.body.classList.toggle("zoomed-out", zoomedOut);
  }
  function queue() { if (raf === null) raf = window.requestAnimationFrame(apply); }
  if (vv.addEventListener) {
    vv.addEventListener("resize", queue);
    vv.addEventListener("scroll", queue);
  }
  window.addEventListener("orientationchange", function () {
    lastW = 0; setTimeout(apply, 150);
  });
  apply();
})();
</script>
"""


def main():
    if not os.path.exists(TARGET):
        sys.exit("找不到 " + TARGET)
    h = io.open(TARGET, encoding="utf-8").read()
    changed = []

    m = re.search(r'<meta\s+name="viewport"\s+content="([^"]*)"', h)
    if m and "viewport-fit" not in m.group(1):
        h = h[:m.start(1)] + m.group(1) + ", viewport-fit=cover" + h[m.end(1):]
        changed.append("viewport 加 viewport-fit=cover")
    elif not m:
        h = h.replace("<head>",
                      '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">',
                      1)
        changed.append("补齐 viewport meta")

    if "text-size-adjust" not in h:
        anchor = "*{margin:0;padding:0;box-sizing:border-box}"
        if anchor in h:
            h = h.replace(anchor, anchor + "\nhtml{-webkit-text-size-adjust:100%;text-size-adjust:100%}", 1)
            changed.append("补 text-size-adjust")
        else:
            idx = h.rfind("</style>")
            if idx == -1:
                sys.exit("找不到 </style>，中止")
            h = h[:idx] + "html{-webkit-text-size-adjust:100%;text-size-adjust:100%}\n" + h[idx:]
            changed.append("补 text-size-adjust（插入 style 末尾）")

    if "max-width:520px" not in h:
        idx = h.rfind("</style>")
        if idx == -1:
            sys.exit("找不到 </style>，中止")
        h = h[:idx] + MEDIA + h[idx:]
        changed.append("注入 @media(max-width:520px)")

    if "visualViewport" not in h:
        idx = h.rfind("</head>")
        if idx == -1:
            sys.exit("找不到 </head>，中止")
        h = h[:idx] + SCRIPT + h[idx:]
        changed.append("注入 visualViewport 自适应脚本")

    if changed:
        io.open(TARGET, "w", encoding="utf-8", newline="").write(h)
        print("已打补丁：")
        for c in changed:
            print("  ->", c)
    else:
        print("无需修改：移动端适配已存在")


if __name__ == "__main__":
    main()
