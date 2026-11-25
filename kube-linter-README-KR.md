# KubeLinter 가이드 (Korean)

이 문서는 쿠버네티스 매니페스트 정적 분석 도구인 **KubeLinter**의 **윈도우(Windows) 환경 설치 방법**, 핵심 개념, 그리고 전체 서브커맨드(Subcommands) 목록과 활용법을 정리한 실습 가이드입니다.

---

## 1. 윈도우(Windows) 버전 KubeLinter 설치 방법

Windows 환경에서 `kube-linter.exe`를 설치하고 설정하는 3가지 방법입니다. 실습 프로젝트에서는 **방법 1(바이너리 직접 다운로드)**을 가장 추천합니다.

### 방법 1: GitHub 공식 릴리스에서 바이너리 다운로드 (권장)

GitHub 저장소의 Release 페이지에서 Windows용 사전 빌드된 바이너리를 다운로드하여 바로 실행할 수 있습니다.

1. **PowerShell에서 원클릭 다운로드 및 압축 해제**:
   PowerShell 터미널을 열고 작업 디렉터리에서 아래 명령어를 실행합니다.
   ```powershell
   # 1. Windows x86_64 바이너리 압축 파일 다운로드 (최신 버전)
   Invoke-WebRequest -Uri "https://github.com/stackrox/kube-linter/releases/latest/download/kube-linter-windows.zip" -OutFile "kube-linter-windows.zip"

   # 2. 현재 디렉터리에 압축 풀기 (kube-linter.exe 생성)
   Expand-Archive -Path "kube-linter-windows.zip" -DestinationPath "." -Force

   # 3. 다운로드한 임시 zip 파일 정리 (선택 사항)
   Remove-Item "kube-linter-windows.zip"
   ```

2. **설치 확인**:
   ```powershell
   .\kube-linter.exe version
   # 출력 예시: KubeLinter 0.8.3 (또는 최신 버전)
   ```

---

### 방법 2: Windows 패키지 매니저(Chocolatey / Scoop) 사용

Windows 패키지 관리 도구가 설치되어 있다면 명령어 한 줄로 전역 설치할 수 있습니다.

* **Winget 사용 시**:
  ```powershell
  winget install -e --id stackrox.kube-linter
  ```

* **Chocolatey 사용 시**:
  ```powershell
  choco install kube-linter
  ```

* **Scoop 사용 시**:
  ```powershell
  scoop install kube-linter
  ```

---

### 방법 3: Go 개발 도구 (`go install`) 사용

로컬 시스템에 Go 언어(Go 1.20+)가 설치되어 있다면 Go 도구 체인을 통해 빌드 및 설치할 수 있습니다.
```powershell
go install golang.stackrox.io/kube-linter/cmd/kube-linter@latest
```

---

### [팁] 전역 명령어(PATH) 등록 방법
현재 작업 디렉터리가 아닌 어떤 폴더에서든 `kube-linter` 명령을 실행하려면, `kube-linter.exe`가 위치한 디렉터리를 시스템 환경 변수 `PATH`에 등록합니다:

```powershell
# 현재 디렉터리를 사용자 환경변수 Path에 영구 등록 (관리자 권한 불필요)
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";" + (Get-Location).Path, [EnvironmentVariableTarget]::User)
```

---

## 2. KubeLinter란 무엇인가?

**KubeLinter**는 Red Hat(구 StackRox)에서 오픈소스로 개발한 **쿠버네티스 매니페스트 정적 분석(Static Analysis / Linter) 도구**입니다.

쿠버네티스 YAML 파일이나 Helm 차트를 실제 클러스터에 배포하기 전에 사전 분석하여, **보안 모범 사례(Security Best Practices)** 및 **운영 모범 사례(Production Readiness)** 준수 여부를 자동으로 점검합니다.

### 주요 특징
* **사전 예방(Shift-Left Security)**: 클러스터 배포 전(개발 단계 또는 CI/CD 파이프라인)에서 보안 취약점과 설정 오류를 감지합니다.
* **50개 이상의 내장 체크 룰**: 루트 권한 실행 방지, 리소스 요청/제한(Requests/Limits) 설정, 민감한 호스트 경로 마운트 차단, 최신(`latest`) 이미지 태그 사용 방지 등을 기본 검사합니다.
* **다양한 대상 지원**: 단일 YAML 파일, 복수 파일, 디렉터리 전체, Helm 차트 분석을 지원합니다.
* **CI/CD 친화적**: JSON, SARIF, 일반 텍스트 등 다양한 출력 형식을 지원하여 GitHub Actions, GitLab CI 등과 손쉽게 연동됩니다.

---

## 3. KubeLinter 서브커맨드(Subcommands) 목록 및 설명

KubeLinter CLI에서 제공하는 전체 서브커맨드 목록입니다.

### 3.1 전체 서브커맨드 요약

| 서브커맨드 | 설명 | 주요 사용 예시 |
| :--- | :--- | :--- |
| **`lint`** | 쿠버네티스 YAML 파일, 디렉터리 또는 Helm 차트를 검사합니다. | `./kube-linter lint GKE-gateway-nip.yaml` |
| **`checks`** | KubeLinter에 내장된 점검(Check) 규칙 목록과 세부 정보를 확인합니다. | `./kube-linter checks list` |
| **`templates`** | 커스텀 체크 룰을 생성할 때 사용할 수 있는 검사 템플릿 목록을 확인합니다. | `./kube-linter templates list` |
| **`version`** | 현재 설치된 KubeLinter의 버전 정보를 출력합니다. | `./kube-linter version` |
| **`completion`** | 셸 자동완성 스크립트를 생성합니다. (bash, zsh, fish, powershell) | `./kube-linter completion powershell` |
| **`help`** | 특정 커맨드 또는 전체 도움말을 출력합니다. | `./kube-linter help lint` |

---

### 3.2 서브커맨드 상세 설명 및 주요 옵션

#### 1) `lint`
KubeLinter의 핵심 명령어로, 대상 매니페스트 파일이나 Helm 차트를 정적 검사합니다.

* **기본 사용법**:
  ```bash
  # 단일 YAML 파일 검사
  ./kube-linter lint manifest.yaml

  # 디렉터리 내 모든 매니페스트 검사
  ./kube-linter lint ./k8s-manifests/

  # Helm 차트 검사
  ./kube-linter lint ./my-helm-chart/
  ```

* **주요 플래그(Flags)**:
  * `--format <format>`: 결과 출력 형식 지정 (`plain`, `json`, `sarif`).
    ```bash
    ./kube-linter lint --format json manifest.yaml
    ```
  * `--config <path>`: 설정 파일(`.kube-linter.yaml`)을 지정하여 특정 룰을 활성화/비활성화하거나 커스텀 룰을 적용합니다.
    ```bash
    ./kube-linter lint --config .kube-linter.yaml manifest.yaml
    ```
  * `--include-check <checks>`: 기본 비활성화된 체크 룰을 추가로 활성화합니다.
  * `--exclude-check <checks>`: 특정 체크 룰을 검사에서 제외합니다.
  * `--do-not-auto-add-defaults`: 기본 내장 룰을 자동으로 활성화하지 않고 사용자가 명시한 룰만 검사합니다.

---

#### 2) `checks`
KubeLinter에 탑재된 검사 규칙(Built-in Checks) 목록과 각 규칙의 상세 설명, 해결 방안(Remediation)을 조회합니다.

* **서브커맨드**:
  * `checks list`: 내장된 모든 체크 룰 목록을 출력합니다.
* **사용 예시**:
  ```bash
  ./kube-linter checks list
  ```
  출력 내용에는 체크 이름(`Name`), 설명(`Description`), 해결 지침(`Remediation`), 기본 활성화 여부(`Enabled by default`) 등이 포함됩니다.

---

#### 3) `templates`
사용자 정의 룰(Custom Checks)을 만들 때 토대가 되는 체크 템플릿(Check Template) 목록을 조회합니다.

* **서브커맨드**:
  * `templates list`: 지원하는 모든 체크 템플릿 목록을 출력합니다.
* **사용 예시**:
  ```bash
  ./kube-linter templates list
  ```

---

#### 4) `version`
현재 사용 중인 KubeLinter 바이너리의 버전 정보를 확인합니다.

* **사용 예시**:
  ```bash
  ./kube-linter version
  ```

---

#### 5) `completion`
다양한 셸 환경에서 자동완성 기능을 사용할 수 있도록 스크립트를 생성합니다.

* **지원 셸**: `bash`, `zsh`, `fish`, `powershell`
* **PowerShell 사용 예시**:
  ```powershell
  ./kube-linter completion powershell | Out-String | Invoke-Expression
  ```

---

#### 6) `help`
명령어 사용법 및 서브커맨드별 옵션을 확인할 때 사용합니다.

* **사용 예시**:
  ```bash
  ./kube-linter help
  ./kube-linter help lint
  ```
