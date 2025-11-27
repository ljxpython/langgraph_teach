
import asyncio



async def demo(a: str, b: str) -> str:
    print("demo 函数被执行")
    return a + b


async def demo2(a: str, b: str) -> str:
    print("demo2 函数被执行")
    return await demo(a, b)

async def demo3(a: str, b: str) -> str:
    print("demo3 函数被执行")
    result =  demo(a, b)
    return result


async def main():
    print("=== 第一次调用 ===")
    res = await demo("a", "b")
    print(f"res: {res}")

    print("\n=== 第二次调用 ===")
    res2 = await demo2("a", "b")
    print(f"res2: {res2}")

    print("\n=== 第三次调用 ===")
    res3 = await demo3("a", "b")
    print(f"res3: {res3}")

    print("\n=== 直接调用协程对象 ===")
    coroutine_obj1 = demo("a", "b")
    print(f"协程对象1: {coroutine_obj1}")

    coroutine_obj2 = demo2("a", "b")
    print(f"协程对象2: {coroutine_obj2}")

if __name__ == '__main__':
    asyncio.run(main())
