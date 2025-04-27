import aiohttp
from bs4 import BeautifulSoup
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Plain

@register("AstrBot_plugin_0721galgame", "mingrixiangnai", "0721galgame游戏搜索插件", "1.0", "https://github.com/mingrixiangnai/0721galgame")
class GalSearchPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Referer': 'https://nn0721.icu/'
        }

    @filter.command("查gal")
    async def search_gal(self, event: AstrMessageEvent):
        '''搜索Gal游戏信息\n用法：/查gal 游戏名称'''
        args = event.message_str.split(maxsplit=1)
        if len(args) < 2:
            yield event.plain_result("请输入要查询的游戏名称，例如：/查gal 千恋万花")
            return

        keyword = args[1]
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # 发送搜索请求并获取HTML
                url = f"https://nn0721.icu/search/{keyword}"
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    html = await resp.text()

            # 解析HTML结构
            soup = BeautifulSoup(html, 'html.parser')
            articles = soup.find_all('div', class_='article')
            
            if not articles:
                yield event.plain_result(f"未找到与「{keyword}」相关的游戏，可能是机器人无法识别到，可以尝试到网站搜索https://nn0721.icu")
                return

            results = []
            for article in articles:
                # 遍历每个article内的所有<a>标签
                for a_tag in article.find_all('a'):
                    # 提取链接并补全域名
                    game_url = a_tag.get('href', '')
                    if not game_url:
                        continue
                    if not game_url.startswith('http'):
                        game_url = f"https://nn0721.icu{game_url}"
                    
                    # 提取标题（从a标签内部查找）
                    title_div = a_tag.find('div', class_='mdui-card-primary-title')
                    if not title_div:
                        continue
                    game_title = title_div.get_text(strip=True)
                    
                    # 去重并保存结果
                    if game_title and game_url:
                        results.append(f"📌 标题：{game_title}\n🔗 链接：{game_url}")

            # 去重处理（防止重复条目）
            unique_results = list({v.split('链接：')[1]: v for v in results}.values())
            
            if not unique_results:
                yield event.plain_result("未找到与「{keyword}」相关的游戏，可能是机器人无法识别到，可以尝试到网站搜索https://nn0721.icu")
                return

            # 返回最多6条结果，因为网站设置第一页显示6条
            reply = f"🔍 找到 {len(unique_results)} 条结果：\n\n" + "\n\n".join(unique_results[:6])
            yield event.plain_result(reply)

        except aiohttp.ClientError as e:
            logger.error(f"网络请求失败: {str(e)}")
            yield event.plain_result("搜索服务暂时不可用，请等待一会再重试")
        except Exception as e:
            logger.error(f"解析异常: {str(e)}", exc_info=True)
            yield event.plain_result("数据解析失败，请联系开发者检查插件或者可以尝试到网站搜索https://nn0721.icu")

    async def terminate(self):
        '''清理资源'''
        pass