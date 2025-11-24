
## 项目介绍

一个基于 langgraph 框架的教学项目

## agent_chat_ui
一个演示demo的前端页面

使用方式：在graph.json 中配置agent

```
{
  "dependencies": ["."],
  "graphs": {
    "agent": {
      "path": "./src/anything_rag_server/agent_rag_async.py:agent"
    }
  },
  "env": ".env",
  "image_distro": "wolfi"
}
```

启动 `start_server.py`

cd 到`agent_chat_ui`目录下，执行` npm run dev` 来启动

界面如下：

![image-20251124151849306](./assets/image-20251124151849306.png)

点击继续，之后进行对话即可

![image-20251124151933211](./assets/image-20251124151933211.png)







## 学习顺序
1. creat_agent,tool,mcp -> 可以查看 src/ui_test_demo

2. 学习ReAct模式可以看下src/ReAct_demo

3. graph -> 可以查看 src/graphs_examples

4. rag相关: 
       多模态,文档解析: 先看src/file_agent
       稍微整合一下,工程化,看src/file_rag
       对于嵌入模型,嵌入向量,及文档检索加上agent -> src/agentic_rag

5. 将rag做成一个小的项目,可以看下easy_rag_server

6. 之后继续优化,我们采用mcp + agent的构建方式可以看下src/rag_chat 和src/mcp_server_rag 
7. 继续优化，mcp_server_rag 是我们自己手写的 demo，当然如果要完成生产机的 rag有很长的路要走，这时，我们对优秀的 rag 库进行封装，封装成 mcp 工具，供我们调用  -> src/anything_rag_server  ,在文档的 readme.md中有详细的说明
8. 





​    

## easy_rag_server

一个简易的rag后台管理系统+前端+对话系统 ，后续应该还会有v2的版本



## 微信交流
<img src="./assets/image-20251121180714902.png" alt="image-20251121180714902" style="zoom:50%;" />



