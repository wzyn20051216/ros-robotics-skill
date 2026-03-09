param(
  [string]$Target = $env:ROS_ROBOTICS_TARGET,
  [string]$Branch = $env:ROS_ROBOTICS_BRANCH
)

if ([string]::IsNullOrWhiteSpace($Target)) {
  $Target = 'auto'
}
if ([string]::IsNullOrWhiteSpace($Branch)) {
  $Branch = 'main'
}

$repoUrl = 'https://github.com/wzyn20051216/ros-robotics-skill.git'
$tempRoot = Join-Path $env:TEMP ('ros-robotics-skill-' + [guid]::NewGuid().ToString('N'))
$repoPath = Join-Path $tempRoot 'ros-robotics-skill'
$pythonCommand = if (Get-Command python3 -ErrorAction SilentlyContinue) { 'python3' } elseif (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { throw '未找到 python 或 python3' }

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
try {
  & git clone --depth 1 --branch $Branch $repoUrl $repoPath
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $repoPath)) {
    throw 'git clone 失败，请检查网络、仓库名或 GitHub 访问权限。'
  }
  & $pythonCommand (Join-Path $repoPath 'scripts\install.py') --source-root $repoPath --target $Target --force
  if ($LASTEXITCODE -ne 0) {
    throw '安装脚本执行失败。'
  }
}
finally {
  if (Test-Path $tempRoot) {
    Remove-Item $tempRoot -Recurse -Force
  }
}
