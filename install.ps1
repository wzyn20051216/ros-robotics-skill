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

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
try {
  git clone --depth 1 --branch $Branch $repoUrl $repoPath | Out-Null
  python (Join-Path $repoPath 'scripts\install.py') --source-root $repoPath --target $Target --force
}
finally {
  if (Test-Path $tempRoot) {
    Remove-Item $tempRoot -Recurse -Force
  }
}
