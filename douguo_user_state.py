# save_state.py
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # 1. 启动一个浏览器，headless=False 确保我们能看到界面进行操作
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 2. 打开豆果的登录页面
        print("正在打开豆果登录页面...")
        await page.goto("https://www.douguo.com/login")
        print("\n" + "="*50)
        print("浏览器已打开，请在浏览器窗口中手动完成登录操作。")
        print("登录成功后，程序会自动检测并保存状态。")
        print("="*50 + "\n")

        # 3. 等待登录成功的信号
        # 登录成功后，通常页面会跳转，并且会出现代表用户头像的元素。
        # 我们就等待这个头像元素出现，作为登录成功的标志。
        # 你可以用浏览器开发者工具查看登录后右上角头像的CSS选择器。
        # 例如，豆果的头像是 <a class="user-avatar">...</a>
        try:
            await page.wait_for_selector("div.myinfo.relative", timeout=120000) # 等待2分钟
            print("✅ 检测到登录成功！")

            # 4. 保存当前上下文的身份验证状态到文件
            await context.storage_state(path="douguo_auth_state.json")
            print(f"身份验证状态已成功保存到 'douguo_auth_state.json' 文件。")

        except Exception as e:
            print(f"❌ 等待登录超时或失败: {e}")
            print("未能保存状态，请重试。")

        finally:
            await browser.close()
            print("浏览器已关闭。")

if __name__ == "__main__":
    asyncio.run(main())