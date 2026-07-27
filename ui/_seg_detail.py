"""主页段详情 drawer 的 HTML 容器 + 客户端 JS — 单独成文件避免 Python 字符串嵌套地狱。"""
from nicegui import ui


def inject():
    """把 drawer 容器 + 点 .seg 调用 /segment_info 的脚本注入主页。"""
    drawer_html = """
    <div id="seg-detail" class="seg-detail" style="display:none">
      <button type="button" class="seg-detail-close" title="关闭">&times;</button>
      <div class="seg-detail-head">
        <span class="material-symbols-outlined seg-detail-icon">horizontal_rule</span>
        <div>
          <div class="seg-detail-range" id="seg-detail-range">&mdash;</div>
          <div class="seg-detail-main" id="seg-detail-main">&mdash;</div>
        </div>
      </div>
      <div class="seg-detail-summary" id="seg-detail-summary"></div>
      <div class="seg-detail-section-title">活动分类</div>
      <div id="seg-detail-breakdown" class="seg-detail-list"></div>
      <div class="seg-detail-section-title">主要应用</div>
      <div id="seg-detail-top-apps" class="seg-detail-list"></div>
      <div class="seg-detail-stats" id="seg-detail-stats"></div>
    </div>
    """
    ui.html(drawer_html, sanitize=False)

    js = r"""
    <script>
    (function(){
      function _esc(s){var d=document.createElement("div");d.textContent=s||"";return d.innerHTML;}
      function _renderDetail(d){
        document.getElementById("seg-detail-range").textContent = d.since_str + " - " + d.until_str;
        var ic=document.querySelector(".seg-detail-icon");
        ic.textContent=d.icon||"horizontal_rule"; ic.style.color=d.color||"#bbc9cd";
        var main=document.getElementById("seg-detail-main");
        main.textContent=(d.empty? "该段暂无记录": d.main_activity);
        main.style.color=d.color||"#bbc9cd";
        var sum=document.getElementById("seg-detail-summary");
        sum.innerHTML = (d.summary? _esc(d.summary):
                         (d.empty? "该段还未采集到数据，可能此时正空闲或程序未运行。":""));
        var bd=document.getElementById("seg-detail-breakdown");
        if(!d.empty && d.breakdown && d.breakdown.length){
          bd.innerHTML=d.breakdown.map(function(b){
            return '<div class="seg-detail-row"><span>' +
              '<span class="seg-detail-swatch" style="background:'+b.color+'"></span>' +
              _esc(b.activity) + '</span><span>' + b.mins + '</span></div>';
          }).join("");
        } else { bd.innerHTML='<div class="caps seg-detail-empty">暂无</div>'; }
        var ta=document.getElementById("seg-detail-top-apps");
        if(!d.empty && d.top_apps && d.top_apps.length){
          ta.innerHTML=d.top_apps.map(function(t){
            return '<div class="seg-detail-row"><span>' + _esc(t.app) +
              '</span><span>' + t.mins + '</span></div>';
          }).join("");
        } else { ta.innerHTML='<div class="caps seg-detail-empty">暂无</div>'; }
        var st=document.getElementById("seg-detail-stats");
        if(d.empty){ st.innerHTML=""; }
        else {
          st.innerHTML='<span class="caps">VLM ' + d.vlm_count + "帧 · 跳过"
            + d.skip_count + " · 兜底" + d.fallback_count + "</span>";
        }
      }
      document.addEventListener("click", function(e){
        var seg = e.target.closest(".seg");
        if(!seg) return;
        var idx = seg.getAttribute("data-idx");
        if(idx === null) return;
        var el = document.getElementById("seg-detail");
        el.style.display = "block";
        document.querySelectorAll(".seg.active").forEach(function(s){s.classList.remove("active");});
        seg.classList.add("active");
        document.getElementById("seg-detail-main").textContent = "加载中...";
        fetch("/segment_info?idx=" + idx)
          .then(function(r){return r.json();})
          .then(_renderDetail)
          .catch(function(){
            document.getElementById("seg-detail-main").textContent = "加载失败";
          });
      });
      document.querySelector(".seg-detail-close").addEventListener("click", function(){
        document.getElementById("seg-detail").style.display = "none";
        document.querySelectorAll(".seg.active").forEach(function(s){s.classList.remove("active");});
      });
    })();
    </script>
    """
    ui.add_body_html(js)