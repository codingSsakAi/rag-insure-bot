/* Feature: 보험 상식 | Purpose: 파일 용도 주석 추가 | Notes: 해당 파일은 보험 상식 기능에 사용됩니다. */
// -*- coding: utf-8 -*-
// navigation_handler.js - 챗봇 네비게이션 상태 관리

console.info("[NAVIGATION-HANDLER] loaded");

class NavigationHandler {
    constructor() {
        this.currentPath = [];
        this.currentLevel = 0;
        this.maxLevel = 3; // 대분류 → 중분류 → 소분류 → 확인
        this.navigationData = null;
        this.selectedOptions = [];
        this.isNavigationMode = false;
    }

    /**
     * 네비게이션 모드 시작
     */
    startNavigation() {
        this.reset();
        this.isNavigationMode = true;
        this.showProgressBar();
        this.loadNavigationLevel();
        console.info("[NAV] Navigation started");
    }

    /**
     * 네비게이션 초기화
     */
    reset() {
        this.currentPath = [];
        this.currentLevel = 0;
        this.selectedOptions = [];
        this.navigationData = null;
        this.hideProgressBar();
        this.isNavigationMode = false;
        console.info("[NAV] Navigation reset");
    }

    /**
     * 진행바 표시
     */
    showProgressBar() {
        try {
            const bar = document.querySelector('.nav-progress');
            if (bar) {
                bar.style.width = '0%';
                bar.parentElement.style.display = 'block';
            }
        } catch (e) {
            console.warn("[NAV] showProgressBar error:", e);
        }
    }

    /**
     * 진행바 숨김
     */
    hideProgressBar() {
        try {
            const bar = document.querySelector('.nav-progress');
            if (bar && bar.parentElement) {
                bar.parentElement.style.display = 'none';
            }
        } catch (e) {
            console.warn("[NAV] hideProgressBar error:", e);
        }
    }

    /**
     * 진행바 업데이트
     */
    updateProgressBar() {
        try {
            const bar = document.querySelector('.nav-progress');
            if (!bar) return;
            const percent = Math.min(100, Math.floor((this.currentPath.length / this.maxLevel) * 100));
            bar.style.width = percent + '%';
        } catch (e) {
            console.warn("[NAV] updateProgressBar error:", e);
        }
    }

    /**
     * 현재 레벨의 네비게이션 데이터 로드
     * [보강] JSON Content-Type 확인
     */
    async loadNavigationLevel() {
        try {
            showTyping();
            
            const response = await fetch('/api/fault/navigation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: JSON.stringify({
                    path: this.currentPath
                })
            });

            let data;
            const ct = response.headers.get('content-type') || '';
            if (ct.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                hideTyping();
                throw new Error('Internal server error occurred');
            }
            hideTyping();

            if (!response.ok || !data.result) {
                throw new Error(data.error || '네비게이션 데이터를 가져올 수 없습니다.');
            }

            this.navigationData = data.result;
            this.renderNavigationLevel();
            this.updateProgressBar();
            
        } catch (error) {
            hideTyping();
            console.error('[NAV] Load error:', error);
            addMsg("bot", `<span class="text-danger">오류: ${error.message}</span>`);
        }
    }

    /**
     * 현재 레벨의 네비게이션 UI 렌더링
     */
    renderNavigationLevel() {
        if (!this.navigationData) return;

        let html = '';
        html += `<div class="navigation-container">`;
        
        // 제목
        html += `<div class="nav-title">${this.navigationData.title}</div>`;

        // 최종 선택인 경우
        if (this.navigationData.is_final) {
            html += this.renderFinalOptions();
        } else {
            // 일반 네비게이션 버튼들
            html += this.renderNavigationButtons();
        }

        // 액션 버튼들
        html += this.renderActionButtons();
        
        html += `</div>`;

        addMsg("bot", html);
        this.attachEventListeners();
    }

    /**
     * 네비게이션 버튼들 렌더링
     */
    renderNavigationButtons() {
        if (!this.navigationData.items) return '';

        let html = `<div class="nav-buttons">`;
        
        this.navigationData.items.forEach(item => {
            html += `
                <button class="nav-button" data-key="${item.key}">
                    <div class="d-flex align-items-center">
                        <i class="${item.icon} me-3"></i>
                        <div class="flex-grow-1">
                            <div class="fw-bold">${item.title}</div>
                            <div class="small text-muted">${item.description}</div>
                        </div>
                        <i class="fas fa-chevron-right icon"></i>
                    </div>
                </button>
            `;
        });
        
        html += `</div>`;
        return html;
    }

    /**
     * 최종 선택 옵션들 렌더링
     */
    renderFinalOptions() {
        if (!this.navigationData.options) return '';

        let html = `
            <div class="mb-3 text-center">
                <i class="${this.navigationData.icon} text-primary me-2"></i>
                <span class="text-muted">${this.navigationData.description}</span>
            </div>
            <div class="nav-buttons final-options">
        `;
        
        this.navigationData.options.forEach((option, index) => {
            html += `
                <button class="nav-button option-button" data-option="${option}" data-index="${index}">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-check-circle me-3 text-success" style="opacity: 0.3;"></i>
                        <div class="flex-grow-1 text-left">
                            ${option}
                        </div>
                    </div>
                </button>
            `;
        });
        
        html += `</div>`;
        return html;
    }

    /**
     * 액션 버튼 렌더링
     */
    renderActionButtons() {
        let html = `<div class="nav-footer">`;

        // 뒤로가기
        if (this.currentLevel > 0 || this.currentPath.length > 0) {
            html += `
                <button class="action-btn secondary" id="nav-back-btn">
                    <i class="fas fa-arrow-left me-1"></i>이전으로
                </button>
            `;
        }

        // 처음으로
        html += `
            <button class="action-btn warning" id="nav-reset-btn">
                <i class="fas fa-redo me-1"></i>처음으로
            </button>
        `;

        // 최종단계: 확인 버튼(처음에는 숨김, 옵션 선택 시 표시)
        if (this.navigationData && this.navigationData.is_final) {
            html += `
                <button class="action-btn primary d-none" id="nav-confirm-btn">
                    <i class="fas fa-search me-1"></i>
                    과실비율 확인하기
                </button>
            `;
        }

        html += `</div>`;
        return html;
    }

    /**
     * 이벤트 리스너 연결
     * [보강] “최신 메시지 카드 범위”에서만 이벤트 바인딩
     */
    attachEventListeners() {
        const scope = this._latestContainer();

        // 네비게이션 버튼 클릭
        scope.querySelectorAll('.nav-button:not(.option-button)').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const key = e.currentTarget.getAttribute('data-key');
                this.selectNavigationItem(key);
            });
        });

        // 옵션 버튼 클릭
        scope.querySelectorAll('.option-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const option = e.currentTarget.getAttribute('data-option');
                const index = e.currentTarget.getAttribute('data-index');
                this.selectOption(option, index, e.currentTarget);
            });
        });

        // 뒤로가기 버튼
        const backBtn = scope.querySelector('#nav-back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => this.goBack());
        }

        // 초기화 버튼
        const resetBtn = scope.querySelector('#nav-reset-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.startNavigation());
        }

        // 확인하기 버튼
        const confirmBtn = scope.querySelector('#nav-confirm-btn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.confirmSelection());
        }
    }

    /**
     * 네비게이션 항목 선택
     */
    selectNavigationItem(key) {
        this.currentPath.push(key);
        this.currentLevel++;
        
        console.info(`[NAV] Selected: ${key}, Path: ${this.currentPath.join(' → ')}, Level: ${this.currentLevel}`);
        
        // 다음 레벨 로드
        this.loadNavigationLevel();
    }

    /**
     * 최종 옵션 선택
     * [보강] 최신 카드 범위에서만 스타일/버튼 표시 변경
     */
    selectOption(option, index, buttonElement) {
        // 이전 선택 초기화
        const scope = this._latestContainer();
        scope.querySelectorAll('.option-button').forEach(btn => {
            btn.classList.remove('selected');
            const icon = btn.querySelector('.fa-check-circle');
            if (icon) icon.style.opacity = '0.3';
        });

        // 현재 버튼 강조
        if (buttonElement) {
            buttonElement.classList.add('selected');
            const icon = buttonElement.querySelector('.fa-check-circle');
            if (icon) icon.style.opacity = '1';
        }

        // 선택 저장
        this.selectedOptions = [{
            option: option,
            index: index
        }];

        // 확인하기 버튼 표시
        const confirmBtn = scope.querySelector('#nav-confirm-btn');
        if (confirmBtn) {
            confirmBtn.classList.remove('d-none');
        }

        console.info(`[NAV] Option selected: ${option}`);
    }

    /**
     * 뒤로가기
     */
    goBack() {
        if (this.currentLevel > 0) {
            this.currentPath.pop();
            this.currentLevel--;
            this.selectedOptions = [];
            
            console.info(`[NAV] Back to level ${this.currentLevel}, Path: ${this.currentPath.join(' → ')}`);
            
            this.loadNavigationLevel();
        }
    }

    /**
     * 최종 선택 확인 및 결과 요청
     * [보강] JSON Content-Type 확인
     */
    async confirmSelection() {
        if (this.selectedOptions.length === 0) {
            alert('옵션을 선택해주세요.');
            return;
        }

        try {
            showTyping();
            
            // 선택된 경로와 옵션을 조합하여 쿼리 생성
            const fullPath = [...this.currentPath];
            const selectedOption = this.selectedOptions[0].option;
            const queryContext = `${fullPath.join(' > ')} > ${selectedOption}`;

            const response = await fetch('/api/fault/answer/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: JSON.stringify({
                    query: queryContext,
                    navigation_context: {
                        path: fullPath,
                        selected_option: selectedOption,
                        is_navigation_query: true
                    }
                })
            });

            let data;
            const ct = response.headers.get('content-type') || '';
            if (ct.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                hideTyping();
                throw new Error('Internal server error occurred');
            }
            hideTyping();

            if (!response.ok || !data.result) {
                throw new Error(data.error || '과실비율 분석에 실패했습니다.');
            }

            const result = data.result;

            // 선택 요약 표시
            const summaryHtml = `
                <div class="result-container">
                    <div class="system-message mb-3">
                        <i class="fas fa-info-circle me-2"></i>
                        선택하신 사고 유형: <strong>${queryContext}</strong>
                    </div>
                </div>
            `;
            addMsg("bot", summaryHtml);

            // 기존 결과 렌더링 로직 재사용
            this.renderDetailedResult(result);

        } catch (error) {
            hideTyping();
            console.error('[NAV] Confirm error:', error);
            addMsg("bot", `<span class="text-danger">오류: ${error.message}</span>`);
        }
    }

    /**
     * 상세 결과 렌더링 (6개 섹션)
     */
    renderDetailedResult(result) {
        const sections = [];

        // (1) 기본 과실비율
        if (result.base_fault || result.base_fault_description) {
            sections.push(`
                <div class="result-card base-fault">
                    <div class="result-card-header"><i class="fas fa-balance-scale me-2"></i>기본 과실비율</div>
                    <div class="result-card-content">
                        ${result.base_fault ? `<div class="fault-ratio"><div class="fault-ratio-main">${result.base_fault}</div><div class="fault-ratio-description">기본 과실비율</div></div>` : ''}
                        ${result.base_fault_description ? `<div class="mt-3">${result.base_fault_description}</div>` : ''}
                    </div>
                </div>
            `);
        }

        // (2) 가감 요소
        if (Array.isArray(result.adjustments) && result.adjustments.length) {
            sections.push(`
                <div class="result-card adjustments">
                    <div class="result-card-header"><i class="fas fa-sliders-h me-2"></i>가감 요소</div>
                    <div class="result-card-content">
                        <ul class="list-unstyled mb-0">
                            ${result.adjustments.map(a => `<li class="mb-1">• ${a}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `);
        }

        // (3) 참고 규정/사례
        if (Array.isArray(result.references) && result.references.length) {
            sections.push(`
                <div class="result-card references">
                    <div class="result-card-header"><i class="fas fa-book me-2"></i>참고 규정/사례</div>
                    <div class="result-card-content">
                        <ul class="list-unstyled mb-0">
                            ${result.references.map(r => `<li class="mb-1">• ${r}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `);
        }

        // (4) 요약
        if (result.summary) {
            sections.push(`
                <div class="result-card summary">
                    <div class="result-card-header"><i class="fas fa-sticky-note me-2"></i>요약</div>
                    <div class="result-card-content">
                        ${result.summary}
                    </div>
                </div>
            `);
        }

        // (5) 추가 질문 (필요 시)
        if (result.needs_more_input && Array.isArray(result.questions) && result.questions.length) {
            sections.push(`
                <div class="result-card followup">
                    <div class="result-card-header"><i class="fas fa-question-circle me-2"></i>추가 확인</div>
                    <div class="result-card-content">
                        <ul class="list-unstyled mb-0">
                            ${result.questions.map(q => `<li class="mb-1">• ${q}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `);
            showTextInput();
            renderQuestions(result.questions);
        }

        // (6) 안내 문구
        sections.push(`
            <div class="result-card notice">
                <div class="result-card-content small text-muted">
                    표시는 예시 기준이며 사고 구체 사정에 따라 달라질 수 있습니다.
                </div>
            </div>
        `);

        addMsg("bot", sections.join(""));
    }

    /**
     * 최근에 렌더된 네비게이션 컨테이너 반환
     * [보강] 최신 메시지 카드 범위 이벤트 바인딩용
     */
    _latestContainer() {
        const all = document.querySelectorAll('.navigation-container');
        return all.length ? all[all.length - 1] : document;
    }
}

// 전역 인스턴스
window.navigationHandler = new NavigationHandler();

// (호환) 예전 코드에서 start()로 부르는 경우 대응
if (!window.navigationHandler.start) {
    window.navigationHandler.start = function() {
        return window.navigationHandler.startNavigation();
    };
}
