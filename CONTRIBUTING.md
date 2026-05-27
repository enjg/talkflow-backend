# Git 开发流程

## 分支策略

```
main (保护分支) ← 只接受 PR 合并
  └── develop (开发主线) ← 日常开发
       └── feat/xxx (功能分支) ← 具体功能
       └── fix/xxx (修复分支) ← bug修复
```

## 规则

1. **main 分支**：永远保持可部署状态，禁止直接 push
2. **develop 分支**：集成分支，功能完成后合并到此
3. **功能分支**：从 develop 创建，完成后 PR 合并回 develop

## 日常开发流程

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feat/home-view

# 2. 开发 + 提交
git add -A
git commit -m "feat: 新增首页 HomeView"

# 3. 推送到远程
git push origin feat/home-view

# 4. 创建 PR (通过 GitHub 或 gh CLI)
gh pr create --base develop --title "feat: 新增首页" --body "功能描述"

# 5. Review 通过后合并
gh pr merge --squash

# 6. 删除功能分支
git checkout develop
git pull origin develop
git branch -d feat/home-view
```

## 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

## 合并到 main

当 develop 稳定后，创建 PR 从 develop → main：

```bash
gh pr create --base main --head develop --title "release: v0.4" --body "版本说明"
```
