const language = document.querySelector('#language');
const searchInput = document.querySelector('#search');
const searchButton = document.querySelector('#search-btn');
const results = document.querySelector('#results');
const count = document.querySelector('#results-count');
const articleView = document.querySelector('#article-view');
const resultsArea = document.querySelector('.results-area');
const headings = {
  en:{hero:'Explore ideas across languages, with sources, identities and transparent coverage.',search:'Search the demonstration…',result:'Explore the demonstration',empty:'No matching demo articles',references:'Source references',fallback:'Displayed in a fallback language',direct:'Direct language coverage',back:'Back to results'},
  fr:{hero:'Explorez les idées entre langues, avec leurs sources, identités et limites de couverture.',search:'Rechercher dans la démonstration…',result:'Explorer la démonstration',empty:'Aucun article de démonstration correspondant',references:'Références des sources',fallback:'Affiché dans une langue de repli',direct:'Contenu dans la langue demandée',back:'Retour aux résultats'},
};
const el=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;};
let latest=0;
const currentLocale=()=>language.value;
const ui=()=>headings[currentLocale()]||headings.en;
async function getJson(url){const response=await fetch(url,{headers:{Accept:'application/json'}});const json=await response.json();if(!response.ok)throw new Error(json.error||'Request failed');return json;}
function error(text){results.replaceChildren(el('p','error-message',text));count.textContent='—';}
function updatedText(){document.documentElement.lang=currentLocale();document.querySelector('#hero-subtitle').textContent=ui().hero;searchInput.placeholder=ui().search;document.querySelector('#results-heading').textContent=ui().result;}
function card(entry){
  const node=el('article','result-card');
  const kicker=el('div','result-kicker','ENCYCLOPEDIA · SYNTHETIC');
  const name=el('h3','result-name',entry.title||'Untitled');
  const summary=el('p','result-summary',entry.summary||'');
  const bottom=el('div','result-bottom');
  bottom.append(el('span','identity-tag',entry.semantic_id),el('span','coverage-tag',entry.display_status==='direct'?'● direct':'◌ fallback'));
  const open=el('button','card-open',currentLocale()==='fr'?'Lire l’article →':'Read article →');
  open.type='button';open.addEventListener('click',()=>showArticle(entry.slug));
  node.append(kicker,name,summary,bottom,open);return node;
}
async function browse(){
  const id=++latest,locale=currentLocale(),q=searchInput.value;
  try{const payload=await getJson(`/api/v1/search?lang=${encodeURIComponent(locale)}&q=${encodeURIComponent(q)}`);if(id!==latest)return;
    articleView.hidden=true;resultsArea.hidden=false;
    const items=payload.results.map(card);
    results.replaceChildren(...(items.length?items:[el('p','no-results',ui().empty)]));
    count.textContent=`${items.length} ${items.length===1?'article':'articles'}`;
  }catch(e){if(id===latest)error(e.message);}
}
async function showArticle(slug){
  const id=++latest;
  try{const item=await getJson(`/api/v1/articles/${encodeURIComponent(slug)}?lang=${encodeURIComponent(currentLocale())}`);if(id!==latest)return;
    const top=el('div','article-top');const back=el('button','article-back','← '+ui().back);back.type='button';back.addEventListener('click',browse);top.append(back,el('span','identity-tag',item.semantic_id));
    const marker=el('div','article-marker',item.display_status==='direct'?ui().direct:`${ui().fallback}: ${item.effective_locale}`);
    const title=el('h2','article-heading',item.title);title.id='article-heading';
    const intro=el('p','article-lead',item.summary);
    const body=el('div','article-body');for(const section of item.sections){const s=el('section','article-section');s.append(el('h3','',section.heading),el('p','',section.body));body.append(s);}
    const sources=el('div','article-sources');sources.append(el('h3','',ui().references));
    for(const ref of item.source_refs){sources.append(el('p','source-entry',`${ref.id} · ${ref.label}`));}
    sources.append(el('p','sources-note','Synthetic references only · No editorial approval or production authority is implied.'));
    articleView.replaceChildren(top,marker,title,intro,body,sources);
    resultsArea.hidden=true;articleView.hidden=false;articleView.scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){error(e.message);}
}
searchButton.addEventListener('click',browse);
searchInput.addEventListener('keydown',e=>{if(e.key==='Enter')browse();});
language.addEventListener('change',()=>{updatedText();browse();});
updatedText();browse();
