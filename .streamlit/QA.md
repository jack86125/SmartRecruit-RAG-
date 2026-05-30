# RAG 系统开发常见问题解答 (Q&A)

本文档记录了在 RAG 系统开发过程中遇到的常见问题、根本原因分析以及相应的解决方案。

---

## Q1: Streamlit 前端启动时出现 `RuntimeError: Tried to instantiate class '__path__._path'`

**问题现象:**

在通过 `streamlit run app.py` 启动应用时，系统可以正常运行，但控制台会打印出一段很长的 `RuntimeError` 报错，信息如下：

```
Examining the path of torch.classes raised:
Traceback (most recent call last):
  File "C:\...\streamlit\watcher\local_sources_watcher.py", line 217, in get_module_paths
    potential_paths = extract_paths(module)
  File "C:\...\streamlit\watcher\local_sources_watcher.py", line 210, in <lambda>
    lambda m: list(m.__path__._path),
  File "C:\...\torch\_classes.py", line 13, in __getattr__
    proxy = torch._C._get_custom_class_python_wrapper(self.name, attr)
RuntimeError: Tried to instantiate class '__path__._path', but it does not exist. Ensure that it is registered via torch::class_
```

---

**解答:**

### 1. 问题分析：根本原因

这个错误是 **Streamlit 和 PyTorch 之间的一个已知兼容性问题**，通常不会影响应用的实际功能，但会在控制台输出烦人的错误日志。

*   **Streamlit 的文件监视器 (File Watcher)**: 为了实现代码热重载（即修改代码后前端自动刷新），Streamlit 会主动监视项目中所有导入的库文件的路径。
*   **PyTorch 的动态加载机制**: `torch` 库的某些子模块（特别是 `torch.classes`）并非标准的 Python 模块。它使用了一种特殊的动态机制来按需注册和加载 C++ 后端的类。
*   **冲突点**: 当 Streamlit 的文件监视器试图按照标准方式去探查 `torch.classes` 的 `__path__` 属性时，触发了 PyTorch 内部的动态加载逻辑。由于 `__path__` 并不是一个在 PyTorch 后端注册的 C++ 类，因此 PyTorch 抛出了 `RuntimeError`。

简单来说，就是 **Streamlit 的热重载机制对 PyTorch 的特殊内部结构“刨根问底”得太深，从而引发了冲突**。

### 2. 解决方案：将 PyTorch 加入监视“黑名单”

最直接有效的解决方案是明确告诉 Streamlit：“**请忽略 `torch` 库的任何文件变动**”。这可以通过 Streamlit 的配置文件来实现。

### 3. 实施步骤

我们通过以下两步解决了这个问题：

**Step 1: 创建 Streamlit 配置目录**

在项目根目录下创建一个名为 `.streamlit` 的文件夹。

```bash
mkdir .streamlit
```

**Step 2: 创建并编辑配置文件**

在 `.streamlit` 文件夹内创建一个名为 `config.toml` 的文件，并写入以下内容：

```toml
[server]
# 将 torch 文件夹加入文件监视器的黑名单
folderWatchBlacklist = ["torch"]
```

完成以上步骤后，**重启 Streamlit 应用** (`streamlit run app.py`)，该错误便不再出现。应用的正常功能和热重载不受影响，因为我们通常不会去修改 `torch` 库的源代码。
