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
let researchMode=false;
let conceptIndex=new Map();
const currentLocale=()=>language.value;
const ui=()=>headings[currentLocale()]||headings.en;
async function getJson(url){const response=await fetch(url,{headers:{Accept:'application/json'}});const json=await response.json();if(!response.ok)throw new Error(json.error||'Request failed');return json;}
function error(text){results.replaceChildren(el('p','error-message',text));count.textContent='—';}
function updatedText(){document.documentElement.lang=currentLocale();document.querySelector('#hero-subtitle').textContent=researchMode?'Educational policy — source-guided research, not yet canonical':ui().hero;searchInput.placeholder=researchMode?'Search 41 UNESCO concepts…':ui().search;document.querySelector('#results-heading').textContent=researchMode?'Educational policy · UNESCO concept index':ui().result;}
function card(entry){
  const node=el('article','result-card');
  const kicker=el('div','result-kicker',researchMode ? 'UNESCO · UNAPPROVED RESEARCH' : 'ENCYCLOPEDIA · SYNTHETIC');
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
    if(researchMode && item.skos_relations){
      const relations=el('section','article-section');
      relations.append(el('h3','','UNESCO SKOS relationships — controlled vocabulary'));
      for(const [kind,ids] of Object.entries(item.skos_relations)){
        if(!ids.length)continue;
        const group=el('p','');group.append(el('strong','',kind+' · '));
        ids.forEach((id,i)=>{
          if(i)group.append(document.createTextNode(' · '));
          const local=conceptIndex.get(id);
          if(local){
            const link=el('button','article-back',local.title);link.type='button';
            link.addEventListener('click',()=>showArticle(local.slug));group.append(link);
          }else group.append(el('span','',`${id} (outside branch)`));
        });
        relations.append(group);
      }
      body.append(relations);
    }
    const sources=el('div','article-sources');sources.append(el('h3','',ui().references));
    for(const ref of item.source_refs){const row=el('p','source-entry');
      row.append(el('span','',`${ref.id} · ${ref.label}${ref.locator?' · '+ref.locator:''} `));
      if (researchMode && /^https:\/\//.test(ref.url||'')) {
        const link=el('a','','View source');link.href=ref.url;link.rel='noopener noreferrer';
        link.target='_blank';row.append(link);
      }
      sources.append(row);}
    if(researchMode && item.claim_proposals?.length){
      const claims=el('section','article-section');
      claims.append(el('h3','','Atomic research proposals — NOT APPROVED'));
      for(const claim of item.claim_proposals){
        claims.append(el('p','',`${claim.id}: ${claim.statement} [${claim.source_id}: ${claim.source_locator}]`));
      }
      body.append(claims);
    }
    sources.append(el('p','sources-note',researchMode ?
      'Source URLs and locators are research leads. No source bytes captured, no KS/KA or equivalence approved. PRIVATE ONLY.' :
      'Synthetic references only · No editorial approval or production authority is implied.'));
    articleView.replaceChildren(top,marker,title,intro,body,sources);
    resultsArea.hidden=true;articleView.hidden=false;articleView.scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){error(e.message);}
}
searchButton.addEventListener('click',browse);
searchInput.addEventListener('keydown',e=>{if(e.key==='Enter')browse();});
language.addEventListener('change',()=>{updatedText();browse();});
async function bootstrap(){
  try{
    const status=await getJson('/api/v1/status');
    researchMode=status.mode==='private-research';
    if(researchMode){
      document.querySelector('.notice').textContent='PRIVATE RESEARCH · 41 UNESCO ANCHORS · NO VERIFIED ARTICLES / NO PUBLIC RELEASE';
      document.querySelector('.hero-hint').textContent='Research preview only: 1 draft, 40 UNESCO anchors, 19 unapproved claims and 6 uncaptured sources.';
      document.querySelector('.about-foot').textContent='No approved KQ/KP/KA/KS assertions and no public publication authorization.';
      document.querySelector('#hero-subtitle').textContent='Explore Educational policy (EN) with SKOS links, source leads and explicit review status.';
      document.querySelector('#language').replaceChildren(new Option('English (research)', 'en'));
      document.querySelector('footer span:last-child').textContent='Private research · NOT FOR PUBLICATION';
      const topology=await getJson('/api/v1/unesco/branch');
      conceptIndex=new Map(topology.concepts.map(c=>[c.id,c]));
    }
  }catch(e){error(e.message);return;}
  updatedText();
  if(researchMode){
    document.querySelector('#hero-subtitle').textContent='Educational policy research: definitions and provenance under review.';
    document.querySelector('#results-heading').textContent='Educational policy · 41 UNESCO concepts';
  }
  browse();
}
bootstrap();
