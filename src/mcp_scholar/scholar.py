from bs4 import BeautifulSoup
import httpx

async def search_scholar(query: str, count: int) -> list[dict]:
    """模拟谷歌学术搜索"""
    params = {
        "q": query,
        "hl": "en",
        "as_sdt": "0,5"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://scholar.google.com/scholar",
            params=params,
            headers={"User-Agent": "MCP Scholar/1.0"}
        )
        resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, 'lxml')
    results = []
    
    for gs_ri in soup.select(".gs_ri"):
        title = gs_ri.select_one(".gs_rt").text
        authors = gs_ri.select_one(".gs_a").text
        abstract = gs_ri.select_one(".gs_rs").text
        citations = gs_ri.select_one(".gs_fl > a") 
        
        results.append({
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "citations": int(citations.text.split()[2]) if citations else 0
        })
        
        if len(results) >= count:
            break
            
    return sorted(results, key=lambda x: -x["citations"])

def parse_profile(html: str, top_n: int) -> list[dict]:
    """解析个人学术主页"""
    soup = BeautifulSoup(html, 'lxml')
    papers = []
    
    for row in soup.select("#gsc_a_b .gsc_a_t"):
        title = row.select_one(".gsc_a_at").text
        citations = row.select_one(".gsc_a_c").text
        year = row.select_one(".gsc_a_y").text
        
        papers.append({
            "title": title,
            "citations": int(citations) if citations.isdigit() else 0,
            "year": year
        })
    
    return sorted(papers, key=lambda x: -x["citations"])[:top_n]
