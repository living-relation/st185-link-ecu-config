<#
.SYNOPSIS
  Repo hygiene for st185-link-ecu-config (DECISIONS R118): sessions never remove their own
  worktree, this script does it afterwards.

.DESCRIPTION
  1. git fetch --prune
  2. fast-forward main (ff-only) in the main checkout, when it is on main and clean
  3. for each worktree under .claude\worktrees\: remove it and delete its local branch when
       - the branch is merged into origin/main, or its remote branch is gone AND GitHub shows
         a merged PR for it (squash-merges are not ancestors, so "gone" alone is not proof),
       - the worktree is clean (no uncommitted or untracked files), and
       - nothing holds the folder open (a rename probe: Windows refuses to rename a folder
         that is some process's current directory).
     Anything else is left alone and printed with the reason.
  4. delete empty leftover folders under .claude\worktrees\ (locked ones are printed).
  Never force-pushes, never pushes, never touches unmerged work or a remote branch.

.EXAMPLE
  powershell -File tools\hygiene.ps1 -WhatIf     # dry run: prints what it would do
  powershell -File tools\hygiene.ps1             # do it
#>
[CmdletBinding(SupportsShouldProcess)]
param(
  # Any path inside the repo (main checkout or a worktree). Default: the current directory.
  [string]$Repo = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'

function Run-Git {
  param([string]$Dir, [Parameter(ValueFromRemainingArguments)][string[]]$GitArgs)
  $out = & git -C $Dir @GitArgs 2>&1
  [pscustomobject]@{ Code = $LASTEXITCODE; Out = ($out | Out-String).Trim() }
}

function Same-Path([string]$a, [string]$b) {
  (($a -replace '/', '\').TrimEnd('\')) -ieq (($b -replace '/', '\').TrimEnd('\'))
}

# --- locate the main checkout (first entry of `git worktree list`) ---
$list = Run-Git $Repo worktree list --porcelain
if ($list.Code -ne 0) { throw "Not a git repo: $Repo`n$($list.Out)" }
$trees = @()
foreach ($block in ($list.Out -split "(?:\r?\n){2,}")) {
  $t = @{ Path = $null; Branch = $null; Locked = $false }
  foreach ($line in ($block -split "\r?\n")) {
    if ($line -like 'worktree *') { $t.Path = ($line.Substring(9) -replace '/', '\') }
    elseif ($line -like 'branch refs/heads/*') { $t.Branch = $line.Substring(18) }
    elseif ($line -like 'locked*') { $t.Locked = $true }
  }
  if ($t.Path) { $trees += [pscustomobject]$t }
}
$main = $trees[0].Path
$wtRoot = Join-Path $main '.claude\worktrees'
$here = (Get-Location).Path
Write-Host "Main checkout: $main"

# --- 1. fetch --prune (remote-tracking refs only; skipped under -WhatIf, refs may be stale) ---
if ($PSCmdlet.ShouldProcess('origin', 'git fetch --prune')) {
  $r = Run-Git $main fetch --prune origin
  if ($r.Code -ne 0) { throw "fetch failed: $($r.Out)" }
}

# --- 2. fast-forward main ---
$mainTree = $trees[0]
if ($mainTree.Branch -ne 'main') {
  Write-Host "main checkout is on '$($mainTree.Branch)', not main: not fast-forwarding."
} elseif ((Run-Git $main status --porcelain --untracked-files=no).Out) {
  Write-Host "main checkout has local changes: not fast-forwarding."
} elseif ($PSCmdlet.ShouldProcess('main', 'git merge --ff-only origin/main')) {
  $r = Run-Git $main merge --ff-only origin/main
  Write-Host "main: $($r.Out.Split("`n")[0])"
  if ($r.Code -ne 0) { Write-Warning "main did not fast-forward (diverged?): left as is." }
}

# --- 3. merged / gone worktrees ---
[void](Run-Git $main worktree prune)
$gh = Get-Command gh -ErrorAction SilentlyContinue
$kept = @()
foreach ($t in $trees | Select-Object -Skip 1) {
  if (-not (Test-Path -LiteralPath $t.Path)) { continue }
  if (-not ($t.Path -like "$wtRoot\*")) { continue }          # only .claude\worktrees\
  $name = Split-Path $t.Path -Leaf
  $b = $t.Branch
  $skip = $null

  if (-not $b) { $skip = 'detached HEAD' }
  elseif ($t.Locked) { $skip = 'worktree is locked (git worktree lock)' }
  elseif (Same-Path $t.Path $here) { $skip = 'this is the current directory' }
  elseif ((Run-Git $t.Path status --porcelain).Out) { $skip = 'uncommitted or untracked files' }
  else {
    $merged = (Run-Git $main merge-base --is-ancestor $b origin/main).Code -eq 0
    if (-not $merged) {
      $track = (Run-Git $main for-each-ref --format='%(upstream:track)' "refs/heads/$b").Out
      if ($track -notlike '*gone*') { $skip = 'branch not merged and still on the remote (or never pushed)' }
      elseif (-not $gh) { $skip = 'remote branch gone but gh is missing, cannot confirm a merged PR' }
      else {
        $pr = & gh pr list --head $b --state merged --json number --jq 'length' 2>$null
        if ("$pr" -notmatch '^[1-9]') { $skip = 'remote branch gone but no merged PR found' }
      }
    }
  }

  if (-not $skip) {                                             # rename probe: is it held open?
    $probe = "$($t.Path).hygiene-probe"
    try {
      if (-not $WhatIfPreference) {
        Rename-Item -LiteralPath $t.Path -NewName (Split-Path $probe -Leaf) -ErrorAction Stop
        Rename-Item -LiteralPath $probe -NewName $name -ErrorAction Stop
      }
    } catch { $skip = 'in use by a process (a session is probably open in it)' }
  }

  if ($skip) { Write-Host "keep   $name [$b]: $skip"; $kept += $name; continue }
  if ($PSCmdlet.ShouldProcess("$($t.Path) + branch $b", 'git worktree remove + git branch -D')) {
    $r = Run-Git $main worktree remove $t.Path
    if ($r.Code -ne 0) { Write-Host "keep   $name [$b]: worktree remove failed: $($r.Out)"; continue }
    # --delete --force (not -D: PowerShell would read -D as the -Dir parameter). Force is needed
    # because squash-merged branches are not ancestors of main.
    $r = Run-Git $main branch --delete --force $b
    if ($r.Code -ne 0) { Write-Warning "removed $name but could not delete branch ${b}: $($r.Out)"; continue }
    Write-Host "removed $name and branch $b"
  }
}

# --- 4. empty leftover folders ---
if (Test-Path -LiteralPath $wtRoot) {
  $known = (Run-Git $main worktree list --porcelain).Out -split "\r?\n" |
    Where-Object { $_ -like 'worktree *' } | ForEach-Object { ($_.Substring(9) -replace '/', '\') }
  foreach ($d in Get-ChildItem -LiteralPath $wtRoot -Directory -Force) {
    if ($known | Where-Object { Same-Path $_ $d.FullName }) { continue }
    if (Get-ChildItem -LiteralPath $d.FullName -Recurse -File -Force) {
      Write-Host "leftover $($d.Name): not empty and not a worktree, left alone"; continue
    }
    if ($PSCmdlet.ShouldProcess($d.FullName, 'remove empty folder')) {
      try { Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction Stop; Write-Host "removed empty folder $($d.Name)" }
      catch { Write-Host "locked  $($d.Name): empty but in use, try again later" }
    }
  }
}
Write-Host "hygiene done."
