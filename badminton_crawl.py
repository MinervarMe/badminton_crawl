# %%
# 想做一个爬虫的东西自动获取每天羽毛球的资讯
# 羽毛球排名收集完毕
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import datetime as dt
import yaml
from tabulate import tabulate


# 定义提取schema
async def extract_ai_news_article(url, schema):
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,  # 替换为实际的目标 URL
            extraction_strategy=extraction_strategy,
            bypass_cache=True,  # 忽略缓存，确保获取最新内容
        )
        if not result.success:
            print("页面爬取失败")
            return
        extracted_data = json.loads(result.extracted_content)
        print(f"成功提取 {len(extracted_data)} 条记录")
    return extracted_data


def info_print(
    result,
    seg_name_map={
        "match": "赛事",
        "news": "资讯",
        "ranking": "排名",
        "person": "人物",
        "bagua": "八卦",
    },
):

    flag = 0
    txt = ""

    def process_txt(txt):
        flag = 1
        txt += "### 🔥" + i.get("title")
        txt += "\n"
        txt += i.get("content", "")
        return flag, txt

    for seg in seg_name_map:
        if result.get(seg):
            txt += f"## 🚀{seg_name_map.get(seg)}\n"
            for i in result.get(seg):
                flag, txt = process_txt(txt)
                txt += "\n"
        txt += "\n"

    return flag, txt


if __name__ == "__main__":
    import regex

    with open("config.yml") as f:
        cfig = yaml.safe_load(f)
    cfig = cfig.get("default")
    date_s = dt.datetime.today().strftime("%Y-%m-%d")
    result = {}
    for i in cfig:
        if dt.datetime.today().weekday() != 1 and i == "ranking":
            continue
        schema = cfig.get(i).get("schema")
        source_result = {}
        for url in cfig.get(i).get("url"):
            iresult = asyncio.run(
                extract_ai_news_article(cfig.get(i).get("url").get(url), schema=schema)
            )
            update_result = []
            for j in iresult[:11]:
                if j.get(
                    "publication_date"
                ):  # 如果有日期，那么判断是否是当天发布的消息
                    if date_s in j.get("publication_date") or "小时前" in j.get(
                        "publication_date"
                    ):
                        j.update({"publication_date": date_s})
                        update_result.append(j)
                else:
                    update_result.append(j)

            source_result.update({url: update_result})
        result.update({i: source_result})

    f_md = open(f"{date_s}.md", mode="w")
    f_md.write(f"# 「{date_s}」🌤️ 羽球资讯\n")
    f_md.write(f"羽球资讯由 <u>宫商角徵羽 李师傅</u> 整理出品\n")
    for i in result:
        f_md.write(f'## 「{cfig.get(i).get("name")}」')
        f_md.write("\n")
        if i != "ranking":
            flag, txt = info_print(result.get(i))
            f_md.write(txt)
            if flag == 0:
                f_md.write(f"♨️今日暂🈚️资讯～\n")
            f_md.write("\n")
        if i == "ranking" and dt.datetime.today().weekday() == 1:
            for j in result.get(i):
                if result.get(i).get(j):
                    j_upper = j.upper()
                    for k in result.get(i).get(j):
                        player = k.get("player")
                        k.update(
                            {
                                "player": "+".join(
                                    regex.findall("[\u4e00-\u9fa5·]+", player)
                                )
                            }
                        )
                    f_md.write(f"### 🚀{j_upper}")
                    f_md.write("\n")
                    f_md.write(
                        tabulate(
                            result.get(i).get(j), tablefmt="github", headers="keys"
                        )
                    )
                    f_md.write("\n")
    f_md.write("---")
# %%
