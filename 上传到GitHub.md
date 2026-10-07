# 上传到 GitHub

这个目录是用于网页一次上传的仓库内容。主数据为无损压缩 CSV，完整补充研究为 ZIP；默认主分析直接读取压缩数据。

1. 在 GitHub 新建一个空仓库，打开 **Upload files**（已有仓库使用 **Add file → Upload files**）。
2. 在 Finder 打开本发布文件夹。按 **Command + Shift + .** 显示隐藏文件，确保 `.github` 和 `.gitignore` 一起选中。
3. 按 **Command + A** 选中文件夹里面的全部内容，拖入上传区域。上传列表应直接显示 `README.md`、`run_all.py`、`src/`、`data/`、`.github/` 等，不应多一层外部文件夹。
4. 填写提交说明，例如 `Initial research release`，点击 **Commit changes** 完成上传。

GitHub 网页每次最多上传 100 个文件，单文件上限 25 MiB；这个版本符合这两项限制。
操作与限制见 [GitHub 官方说明](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)。

上传后 README 会作为项目首页显示，GitHub Actions 将按配置运行自动检查。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tested.txt
python run_all.py
```

补充材料需要单独使用时，在仓库根目录解压：

```bash
python -m zipfile -e supplementary.zip .
```

补充材料的运行条件见 [supplementary/README.md](supplementary/README.md)。
