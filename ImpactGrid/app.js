const $ = s => document.querySelector(s);
const state = { token: localStorage.getItem("impactgrid_token") || "", user: null, modules: [], authMode: "login" };
const icons = {"PS-01":"🌱","PS-02":"🩸","PS-03":"🧠","PS-04":"🛡️","PS-05":"🧵","PS-06":"🧰","PS-07":"🤝","PS-08":"🧭","PS-09":"⚡","PS-10":"💬","PS-11":"🏫"};
function esc(s=""){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
let toastTimer;
function toast(msg){const t=$("#toast");t.textContent=msg;t.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove("show"),2800);}
async function api(path, options={}) {
  const headers={"Content-Type":"application/json",...(options.headers||{})};
  if(state.token) headers.Authorization="Bearer "+state.token;
  const res=await fetch(path,{...options,headers});
  const data=await res.json().catch(()=>({detail:"Unexpected server response"}));
  if(!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}
const solutionGrid=$("#solutionGrid");
async function loadModules(){
 try { state.modules=await api("/api/modules"); renderModules(); }
 catch(e){solutionGrid.innerHTML='<p class="muted">Could not connect to backend. Start the FastAPI server and refresh.</p>';}
}
function renderModules(){
 const q=$("#searchInput").value.trim().toLowerCase(), cat=$("#categoryFilter").value;
 const filtered=state.modules.filter(m=>(!cat||m.category===cat)&&(!q||[m.id,m.title,m.category,m.description].join(" ").toLowerCase().includes(q)));
 const cats=[...new Set(state.modules.map(m=>m.category))].sort();
 const old=$("#categoryFilter").value;
 $("#categoryFilter").innerHTML='<option value="">All categories</option>'+cats.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join("");
 $("#categoryFilter").value=cats.includes(old)?old:"";
 solutionGrid.innerHTML=filtered.length?filtered.map(m=>`<article class="solution-card"><div class="card-top"><span class="ps-tag">${esc(m.id)}</span><span class="category-tag">${esc(m.category)}</span></div><div class="solution-icon">${icons[m.id]||"✳"}</div><h3>${esc(m.title)}</h3><p>${esc(m.description)}</p><div class="card-bottom"><span class="difficulty">Difficulty: <b>${esc(m.difficulty)}</b></span><button class="open-module" data-module="${esc(m.id)}">Try demo ↗</button></div></article>`).join(""):'<p class="muted">No solutions match your search.</p>';
 solutionGrid.querySelectorAll("[data-module]").forEach(b=>b.addEventListener("click",()=>openModule(b.dataset.module)));
}
function openModule(id){
 const map={"PS-01":"cropName","PS-03":"studyQuestion","PS-04":"quizQuestion","PS-02":"recordKind","PS-05":"recordKind","PS-06":"recordKind","PS-07":"recordKind","PS-08":"recordKind","PS-09":"recordKind","PS-10":"recordKind","PS-11":"recordKind"};
 if(id==="PS-01") $("#recordKind").value="community_issue";
 if(id==="PS-02") $("#recordKind").value="donor_profile";
 if(id==="PS-05") $("#recordKind").value="artisan_product";
 if(id==="PS-06") $("#recordKind").value="service_booking";
 if(id==="PS-07") $("#recordKind").value="community_issue";
 if(id==="PS-09") $("#recordKind").value="study_plan";
 if(id==="PS-10") $("#recordKind").value="faculty_feedback";
 if(id==="PS-11") $("#recordKind").value="campus_task";
 if(id==="PS-08") toast("Career Explorer: compare skills, projects and learning paths in your saved action.");
 document.querySelector("#workspace").scrollIntoView({behavior:"smooth"});
 const target=map[id]; if(target && id!=="PS-02" && id!=="PS-05" && id!=="PS-06" && id!=="PS-07" && id!=="PS-08" && id!=="PS-09" && id!=="PS-10" && id!=="PS-11") setTimeout(()=>$("#"+target).focus(),350);
}
$("#searchInput").addEventListener("input",renderModules);
$("#categoryFilter").addEventListener("change",renderModules);
$("#menuToggle").addEventListener("click",()=>$("#topNav")?.classList.toggle("open"));
document.querySelectorAll(".topbar nav a").forEach(a=>a.addEventListener("click",()=>document.querySelector(".topbar nav").classList.remove("open")));

function setAuthUI(){
 const area=$("#authArea");
 if(state.user){area.innerHTML=`<span class="user-status">Hi, ${esc(state.user.name)}</span><button class="btn btn-light" id="logoutBtn">Sign out</button>`;$("#logoutBtn").onclick=logout;$("#userStatus").textContent="Signed in as "+state.user.email;loadRecords();}
 else {area.innerHTML='<button class="btn btn-light" id="loginOpen">Sign in</button><button class="btn btn-primary" id="signupOpen">Get started</button>';$("#loginOpen").onclick=()=>openAuth("login");$("#signupOpen").onclick=()=>openAuth("signup");$("#userStatus").textContent="Guest mode · demo data";$("#recordsList").innerHTML='<p class="muted">Sign in to view saved records.</p>';}
}
function openAuth(mode){state.authMode=mode;$("#authModal").classList.remove("hidden");$("#authTitle").textContent=mode==="login"?"Welcome back":"Create your account";$("#authSubtitle").textContent=mode==="login"?"Sign in to save your work.":"Create an account to keep your actions in the database.";$("#nameWrap").classList.toggle("hidden",mode==="login");$("#authName").required=mode==="signup";$("#authSubmit").textContent=mode==="login"?"Sign in":"Create account";$("#switchText").textContent=mode==="login"?"New here?":"Already have an account?";$("#switchAuth").textContent=mode==="login"?"Create account":"Sign in";$("#authMessage").textContent="";}
$("#loginOpen").onclick=()=>openAuth("login");$("#signupOpen").onclick=()=>openAuth("signup");
$("#modalClose").onclick=()=>$("#authModal").classList.add("hidden");
$("#authModal").addEventListener("click",e=>{if(e.target.id==="authModal")$("#authModal").classList.add("hidden")});
$("#switchAuth").onclick=()=>openAuth(state.authMode==="login"?"signup":"login");
$("#authForm").addEventListener("submit",async e=>{
 e.preventDefault();const mode=state.authMode;$("#authMessage").textContent="Working…";
 try{const data=await api(mode==="login"?"/api/login":"/api/signup",{method:"POST",body:JSON.stringify({name:$("#authName").value,email:$("#authEmail").value,password:$("#authPassword").value})});state.token=data.token;state.user=data.user;localStorage.setItem("impactgrid_token",state.token);$("#authModal").classList.add("hidden");setAuthUI();toast(mode==="login"?"Signed in successfully":"Account created successfully");}
 catch(err){$("#authMessage").textContent=err.message;}
});
async function logout(){try{await api("/api/logout",{method:"POST"});}catch(e){}state.token="";state.user=null;localStorage.removeItem("impactgrid_token");setAuthUI();toast("Signed out.");}
async function restoreSession(){if(!state.token){setAuthUI();return;}try{state.user=await api("/api/me");}catch(e){state.token="";localStorage.removeItem("impactgrid_token");}setAuthUI();}
$("#studyAsk").onclick=async()=>{
 const question=$("#studyQuestion").value.trim();if(!question){toast("Enter a study question first.");return;}
 const b=$("#studyAsk");b.disabled=true;b.textContent="Thinking…";$("#studyResult").classList.remove("hidden");$("#studyResult").textContent="Preparing an explanation…";
 try{const r=await api("/api/ai/study",{method:"POST",body:JSON.stringify({question,language:$("#studyLanguage").value,notes:$("#studyNotes").value})});$("#studyResult").textContent=r.answer+"\n\nMode: "+r.mode;}
 catch(e){$("#studyResult").textContent=e.message;}finally{b.disabled=false;b.textContent="Explain this topic ↗";}
};
$("#cropAsk").onclick=async()=>{
 const crop=$("#cropName").value.trim(),symptoms=$("#cropSymptoms").value.trim();if(!crop||!symptoms){toast("Enter crop and symptoms.");return;}
 const b=$("#cropAsk");b.disabled=true;b.textContent="Checking…";
 try{const r=await api("/api/ai/crop-check",{method:"POST",body:JSON.stringify({crop,symptoms})});$("#cropResult").classList.remove("hidden");$("#cropResult").textContent="Crop: "+r.crop+"\nPossible cause: "+r.possible_cause+"\n\nSuggested next steps:\n• "+r.actions.join("\n• ")+"\n\nImportant: "+r.disclaimer;}
 catch(e){toast(e.message);}finally{b.disabled=false;b.textContent="Check symptoms ↗";}
};
document.querySelectorAll(".quiz-options button").forEach(btn=>btn.onclick=()=>{
 const f=$("#quizFeedback");if(btn.dataset.correct==="true"){f.textContent="Correct! Never share an OTP. Contact your bank using its official app or number.";f.style.color="#287345";}
 else{f.textContent="Not safe. A legitimate bank should never ask you to disclose your OTP.";f.style.color="#a34131";}
});
$("#saveRecord").onclick=async()=>{
 if(!state.user){openAuth("login");$("#recordFeedback").classList.remove("hidden");$("#recordFeedback").textContent="Sign in to save actions to the database.";return;}
 const title=$("#recordTitle").value.trim(),description=$("#recordDescription").value.trim();
 if(!title||!description){toast("Add a title and description.");return;}
 const b=$("#saveRecord");b.disabled=true;
 try{await api("/api/records",{method:"POST",body:JSON.stringify({kind:$("#recordKind").value,data:{title,description}})});$("#recordFeedback").classList.remove("hidden");$("#recordFeedback").textContent="Saved to the database successfully.";$("#recordTitle").value="";$("#recordDescription").value="";await loadRecords();toast("Action saved.");}
 catch(e){toast(e.message);}finally{b.disabled=false;}
};
async function loadRecords(){
 if(!state.user)return;
 try{const records=await api("/api/records");const mine=records.filter(r=>r.owner_id===state.user.id);
 $("#recordsList").innerHTML=mine.length?mine.slice(0,8).map(r=>`<div class="record-item"><div><b>${esc(r.data.title||r.kind)}</b><small>${esc(r.kind.replaceAll("_"," "))} · ${esc(r.data.description||"")}</small></div><button class="text-button" data-delete="${r.id}">Delete</button></div>`).join(""):'<p class="muted">No saved actions yet. Create your first one above.</p>';
 $("#recordsList").querySelectorAll("[data-delete]").forEach(b=>b.onclick=async()=>{try{await api("/api/records/"+b.dataset.delete,{method:"DELETE"});await loadRecords();toast("Record deleted.");}catch(e){toast(e.message);}});
 }catch(e){$("#recordsList").innerHTML='<p class="muted">Could not load saved actions.</p>';}
}
$("#refreshRecords").onclick=loadRecords;
restoreSession();loadModules();
