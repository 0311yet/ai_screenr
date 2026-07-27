"""主页「生成日报」按钮的 modal：日期下拉 + 报告内容（md→HTML）+ 下载 + 关闭。纯前端 DOM + fetch，无外部依赖。"""
from nicegui import ui


def inject():
    modal_html = """
    <div id="report-modal" class="report-modal" style="display:none">
      <div class="report-modal-backdrop"></div>
      <div class="report-modal-card">
        <div class="report-modal-head">
          <div>
            <div class="report-modal-title">
              <span class="material-symbols-outlined">description</span>活动日报
            </div>
            <div class="report-modal-sub caps">按 10 分钟段聚合 · 当日各类活动占比与时间线</div>
          </div>
          <div class="report-modal-actions">
            <select id="report-date-select" class="report-date-select"></select>
            <a id="report-download" class="report-dl-btn" title="下载 .md">
              <span class="material-symbols-outlined">download</span>
            </a>
            <button type="button" class="report-modal-close" title="关闭">&times;</button>
          </div>
        </div>
        <div id="report-body" class="report-body">
          <div class="caps" style="opacity:.6">加载中...</div>
        </div>
      </div>
    </div>
    """
    ui.html(modal_html, sanitize=False)

    js = r"""
    <script>
    (function(){
      function _esc(s){var d=document.createElement("div");d.textContent=s==null?"":s;return d.innerHTML;}
      // 极简 md→html（只处理日报用到的 #/##/- **/段落）
      function _mdToHtml(md){
        if(!md) return '<div class="caps" style="opacity:.6">该日期无活动数据。</div>';
        return md.split("\n").map(function(line){
          if(line.indexOf("# ")===0) return '<h3 class="rp-h1">'+_esc(line.slice(2))+'</h3>';
          if(line.indexOf("## ")===0) return '<div class="rp-h2">'+_esc(line.slice(3))+'</div>';
          if(line.indexOf("- ")===0){
            var t=_esc(line.slice(2)).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>');
            return '<div class="rp-li">'+t+'</div>';
          }
          if(line.trim()==="") return "";
          var t=_esc(line).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>');
          return '<div class="rp-p">'+t+'</div>';
        }).join("");
      }
      function _fillDates(){
        var sel=document.getElementById("report-date-select");
        var today=new Date(); var opts=[];
        for(var i=0;i<7;i++){
          var d=new Date(today.getTime()-i*86400000);
          var y=d.getFullYear(), m=("0"+(d.getMonth()+1)).slice(-2), day=("0"+d.getDate()).slice(-2);
          var iso=y+"-"+m+"-"+day;
          var label=(i===0?"今天":i===1?"昨天":iso);
          opts.push('<option value="'+iso+'">'+label+" · "+iso+'</option>');
        }
        sel.innerHTML=opts.join("");
      }
      function _load(date){
        var body=document.getElementById("report-body");
        body.innerHTML='<div class="caps" style="opacity:.6">生成中...</div>';
        document.getElementById("report-download").href="/report_file?date="+encodeURIComponent(date);
        _load.token=(window._rpToken||0)+1; window._rpToken=_load.token;
        var myToken=_load.token;
        fetch("/generate_report?date="+encodeURIComponent(date),{method:"POST"})
          .then(function(r){return r.json();})
          .then(function(d){
            if(myToken!==window._rpToken) return;  // 已有更新的请求，丢弃
            if(!d.ok){ body.innerHTML='<div class="caps" style="color:#f87171">生成失败：'+_esc(d.error||"")+'</div>'; return; }
            body.innerHTML=_mdToHtml(d.md);
          })
          .catch(function(){ if(myToken===window._rpToken) body.innerHTML='<div class="caps" style="color:#f87171">网络错误</div>'; });
      }
      function _open(){
        _fillDates();
        var sel=document.getElementById("report-date-select");
        // 默认选「今天」，若今天还没数据也没关系，用户可切换
        sel.value=sel.options[0].value;
        document.getElementById("report-modal").style.display="flex";
        _load(sel.value);
      }
      function _close(){ document.getElementById("report-modal").style.display="none"; }

      // 点顶部「生成日报」按钮打开、关闭、切日期 均用 document 委托
      // （因为 modal DOM 由 NiceGUI 异步注入，脚本运行时元素可能还不存在）
      document.addEventListener("click", function(e){
        if(e.target.closest(".report-btn")){ _open(); return; }
        if(e.target.closest(".report-modal-close")||e.target.closest(".report-modal-backdrop")){ _close(); return; }
        if(e.target.closest(".report-dl-btn")){ /* 让 <a> 默认下载行为生效 */ return; }
      });
      document.addEventListener("change", function(e){
        if(e.target && e.target.id==="report-date-select"){ _load(e.target.value); }
      });
      document.addEventListener("keydown", function(e){ if(e.key==="Escape") _close(); });
    })();
    </script>
    """
    ui.add_body_html(js)