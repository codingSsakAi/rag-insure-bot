/**
 * 플로팅 액션 버튼 컨트롤러
 * 스크롤 추적, 확장/수축, 상태 관리
 * - 우하단 레거시 햄버거 FAB(#ip-fab 등) 강제 숨김
 * - floating-fab 마크업이 없으면 sideActions로 자동 폴백
 * - floating-fab이 있을 때만 .side-actions 숨김(중복 노출 방지)
 * - 아이콘 폰트 실패 시 인라인 SVG/문자 폴백 주입
 */

class FloatingFABController {
  constructor() {
    this.fabContainer = null;
    this.mainToggle = null;
    this.subContainer = null;
    this.actionItems = [];
    this.isExpanded = false;
    this.activeAction = null;
    this.scrollTimeout = null;
    this.lastScrollY = window.scrollY;
    this.debugMode = false;

    // 바인딩을 위해 메서드 바인드
    this.executeClaimKnowledge = this.executeClaimKnowledge.bind(this);
    this.executeGuide = this.executeGuide.bind(this);
    this.executeKnowhow = this.executeKnowhow.bind(this);
    this.executeChatbot = this.executeChatbot.bind(this);

    this.init();
  }

  /** 레거시 우하단 햄버거 FAB 숨김 */
  hideLegacyHamburger() {
    ['ip-fab', 'ip-panel', 'ip-overlay'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.style.setProperty('display', 'none', 'important');
        el.style.setProperty('visibility', 'hidden', 'important');
      }
    });
  }

  /** 아이콘 폰트 실패 시 폴백(인라인 SVG 또는 문자) 주입 */
  ensureIconVisibility() {
    try {
      // 메인 토글
      if (this.mainToggle) {
        const hasVisibleIcon = !!this.mainToggle.querySelector('.icon-ms, .fa, .fas, .fab, .far, .fa-solid, .material-symbols-outlined');
        if (!hasVisibleIcon) {
          // 폴백: + 문자
          const span = document.createElement('span');
          span.textContent = '+';
          span.setAttribute('aria-hidden', 'true');
          span.style.fontSize = '20px';
          span.style.lineHeight = '1';
          this.mainToggle.appendChild(span);
        }
      }

      // 서브 버튼들
      const subBtns = document.querySelectorAll('.fab-sub-btn');
      subBtns.forEach(btn => {
        const hasIcon = !!btn.querySelector('.icon-ms, .fa, .fas, .fab, .far, .fa-solid, .material-symbols-outlined, svg');
        if (!hasIcon) {
          // 간단한 원형 점 SVG 폴백
          const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
          svg.setAttribute('viewBox', '0 0 24 24');
          svg.style.width = '20px';
          svg.style.height = '20px';
          svg.setAttribute('aria-hidden', 'true');
          const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          c.setAttribute('cx', '12'); c.setAttribute('cy', '12'); c.setAttribute('r', '5');
          c.setAttribute('fill', 'currentColor');
          svg.appendChild(c);
          btn.prepend(svg);
        }
      });
    } catch (e) {
      console.warn('아이콘 폴백 주입 중 오류:', e);
    }
  }

  /** floating-fab이 없을 때 사이드 FAB로 동작 폴백 */
  bindSideFallback() {
    const bind = (id, fn) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('click', fn, { passive: true });
    };
    bind('claim-knowledge-fab', this.executeClaimKnowledge);
    bind('guide-fab', this.executeGuide);
    bind('weekly-fab', this.executeKnowhow);
    bind('chatbot-fab', this.executeChatbot);

    // 아이콘 폴백도 적용
    this.ensureIconVisibility();

    if (this.debugMode) console.log('사이드 FAB 폴백 바인딩 완료');
  }

  init() {
    try {
      // 0) 레거시 우하단 햄버거 FAB 숨김 (항상)
      this.hideLegacyHamburger();

      // 1) DOM 요소 찾기
      this.fabContainer = document.getElementById('floating-fab');
      this.mainToggle = document.getElementById('fab-main-toggle');
      this.subContainer = document.getElementById('fab-sub-actions');
      this.actionItems = document.querySelectorAll('.fab-action-item');

      // 2) 우측 중앙 FAB 마크업이 없으면 사이드 FAB로 폴백
      if (!this.fabContainer || !this.mainToggle) {
        console.warn('floating-fab이 없어 sideActions로 폴백합니다.');
        // 절대 사이드 FAB를 숨기지 말고, 클릭 바인딩만 해준다.
        this.preventEventConflicts();     // 충돌 최소화
        this.initModalStateTracking();    // 상태 동기화(가능한 범위)
        this.bindSideFallback();          // 폴백 바인딩
        // 디버그 모드
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
          this.enableDebugMode();
        }
        return;
      }

      // 3) (우측 중앙 FAB가 있을 때만) 레거시/사이드 FAB 숨김
      this.disableLegacyFABs(true);

      // 4) 이벤트 충돌 방지 & 모달 상태 추적
      this.preventEventConflicts();
      this.initModalStateTracking();

      // 5) 기본 초기화
      this.bindEvents();
      this.initScrollTracking();

      // 6) 아이콘 폴백(폰트 실패 대비)
      this.ensureIconVisibility();

      // 7) 디버그 모드 (개발 시에만)
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        this.enableDebugMode();
      }

      console.log('FloatingFAB Controller 초기화 완료');
    } catch (error) {
      this.handleError(error, 'init');
    }
  }

  bindEvents() {
    try {
      // 메인 토글 버튼 클릭
      this.mainToggle.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleExpansion();
      });

      // 서브 버튼 클릭 (기능 실행)
      this.actionItems.forEach(item => {
        const button = item.querySelector('.fab-sub-btn');
        const action = item.dataset.action;

        if (button && action) {
          button.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleActionClick(action, item);
          });
        }
      });

      // 라벨 클릭 (서브 버튼과 동일한 동작)
      this.actionItems.forEach(item => {
        const label = item.querySelector('.fab-label');
        const action = item.dataset.action;

        if (label && action) {
          label.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleActionClick(action, item);
          });
        }
      });

      // 외부 클릭 시 접기
      document.addEventListener('click', (e) => {
        try {
          if (!this.fabContainer.contains(e.target) && this.isExpanded) {
            this.collapseActions();
          }
        } catch (error) {
          console.warn('외부 클릭 처리 중 오류:', error);
        }
      });

      // ESC 키로 접기
      document.addEventListener('keydown', (e) => {
        try {
          if (e.key === 'Escape' && this.isExpanded) {
            this.collapseActions();
          }
        } catch (error) {
          console.warn('키보드 이벤트 처리 중 오류:', error);
        }
      });
    } catch (error) {
      this.handleError(error, 'bindEvents');
    }
  }

  initScrollTracking() {
    try {
      // 스크롤 이벤트 리스너
      window.addEventListener('scroll', () => {
        this.handleScroll();
      }, { passive: true });

      // 리사이즈 이벤트 (뷰포트 변경 시 위치 재조정)
      window.addEventListener('resize', () => {
        this.adjustPosition();
      });

      // 초기 위치 설정
      this.adjustPosition();
    } catch (error) {
      this.handleError(error, 'initScrollTracking');
    }
  }

  handleScroll() {
    try {
      const currentScrollY = window.scrollY;
      const scrollDelta = currentScrollY - this.lastScrollY;

      // 스크롤 방향에 따른 FAB 위치 조정
      this.updateFABPosition(scrollDelta);

      this.lastScrollY = currentScrollY;

      // 스크롤 중일 때는 확장된 상태를 접기
      if (this.isExpanded) {
        clearTimeout(this.scrollTimeout);
        this.scrollTimeout = setTimeout(() => {
          // 스크롤 멈춤 후 대기 (필요 시 동작 추가)
        }, 150);
      }
    } catch (error) {
      console.warn('스크롤 처리 중 오류:', error);
    }
  }

  updateFABPosition(scrollDelta) {
    try {
      const viewportHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      const scrollProgress = (documentHeight - viewportHeight) > 0
        ? window.scrollY / (documentHeight - viewportHeight)
        : 0;

      // 스크롤 진행률에 따라 FAB 위치 조정 (30% ~ 70% 범위에서 움직임)
      const minPosition = 30; // 뷰포트 상단으로부터 30%
      const maxPosition = 70; // 뷰포트 상단으로부터 70%
      const positionRange = maxPosition - minPosition;
      const newPosition = minPosition + (scrollProgress * positionRange);

      this.fabContainer.style.top = `${newPosition}%`;
      this.fabContainer.style.bottom = 'auto';
      this.fabContainer.style.transform = 'translateY(-50%)';
    } catch (error) {
      console.warn('FAB 위치 업데이트 중 오류:', error);
    }
  }

  adjustPosition() {
    try {
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      this.fabContainer.style.position = 'fixed';
      this.fabContainer.style.display = 'block';
      this.fabContainer.style.visibility = 'visible';

      if (viewportWidth < 768) {
        this.fabContainer.style.right = '16px';
      } else {
        this.fabContainer.style.right = '24px';
      }

      // 초기 중앙 고정
      this.fabContainer.style.top = '50%';
      this.fabContainer.style.transform = 'translateY(-50%)';

      if (viewportHeight < 600) {
        this.fabContainer.style.top = '40%';
      }
    } catch (error) {
      console.warn('위치 조정 중 오류:', error);
    }
  }

  toggleExpansion() {
    try {
      if (this.isExpanded) {
        this.collapseActions();
      } else {
        this.expandActions();
      }
    } catch (error) {
      this.handleError(error, 'toggleExpansion');
    }
  }

  expandActions() {
    try {
      this.isExpanded = true;
      this.fabContainer.classList.add('expanded');
      this.mainToggle.setAttribute('aria-label', '메뉴 닫기');
      this.mainToggle.setAttribute('aria-expanded', 'true');

      // 백드롭 표시
      document.body.classList.add('fab-backdrop-active');

      this.announceToScreenReader('메뉴가 열렸습니다');
      if (this.debugMode) console.log('FAB 확장됨 (반원 배치)');
    } catch (error) {
      this.handleError(error, 'expandActions');
    }
  }

  collapseActions() {
    try {
      this.isExpanded = false;
      this.fabContainer.classList.remove('expanded');
      this.mainToggle.setAttribute('aria-label', '메뉴 열기');
      this.mainToggle.setAttribute('aria-expanded', 'false');

      // 백드롭 제거
      document.body.classList.remove('fab-backdrop-active');

      if (this.activeAction) this.clearActiveAction();
      this.announceToScreenReader('메뉴가 닫혔습니다');
      if (this.debugMode) console.log('FAB 접힘됨');
    } catch (error) {
      this.handleError(error, 'collapseActions');
    }
  }

  handleActionClick(action, itemElement) {
    try {
      // 이전 활성화 해제
      if (this.activeAction) {
        this.clearActiveAction();
      }

      // 새로운 액션 활성화
      this.setActiveAction(action, itemElement);

      // 기능 실행
      this.executeActionEnhanced(action);

      // 잠시 후 메뉴 접기
      setTimeout(() => {
        this.collapseActions();
      }, 300);
    } catch (error) {
      this.handleError(error, 'handleActionClick');
    }
  }

  setActiveAction(action, itemElement) {
    try {
      this.activeAction = action;
      itemElement.classList.add('active');

      // 접근성
      const button = itemElement.querySelector('.fab-sub-btn');
      if (button) {
        button.setAttribute('aria-pressed', 'true');
      }

      if (this.debugMode) {
        console.log(`Active action set: ${action}`);
      }
    } catch (error) {
      this.handleError(error, 'setActiveAction');
    }
  }

  clearActiveAction() {
    try {
      if (this.activeAction) {
        const activeItem = document.querySelector(`[data-action="${this.activeAction}"]`);
        if (activeItem) {
          activeItem.classList.remove('active');
          const button = activeItem.querySelector('.fab-sub-btn');
          if (button) {
            button.setAttribute('aria-pressed', 'false');
          }
        }

        if (this.debugMode) {
          console.log(`Active action cleared: ${this.activeAction}`);
        }

        this.activeAction = null;
      }
    } catch (error) {
      this.handleError(error, 'clearActiveAction');
    }
  }

  // 모달 상태 감지 및 동기화
  initModalStateTracking() {
    try {
      // Bootstrap 모달 이벤트 감지
      const bootstrapModals = ['guideModal', 'knowhowModal', 'claimKnowledgeModal'];

      bootstrapModals.forEach(modalId => {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
          modalElement.addEventListener('shown.bs.modal', () => {
            this.syncActiveState(this.getActionByModalId(modalId));
          });

          modalElement.addEventListener('hidden.bs.modal', () => {
            this.clearActiveAction();
          });
        }
      });

      // 챗봇 패널 상태 감지
      const chatbotContainer = document.getElementById('chatbot-container');
      if (chatbotContainer) {
        const chatbotObserver = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
              const display = window.getComputedStyle(chatbotContainer).display;
              if (display !== 'none') {
                this.syncActiveState('chatbot');
              } else {
                this.clearActiveAction();
              }
            }
          });
        });

        chatbotObserver.observe(chatbotContainer, {
          attributes: true,
          attributeFilter: ['style']
        });
      }
    } catch (error) {
      this.handleError(error, 'initModalStateTracking');
    }
  }

  // 모달 ID로 액션 타입 찾기
  getActionByModalId(modalId) {
    const modalActionMap = {
      'guideModal': 'guide',
      'knowhowModal': 'knowhow',
      'claimKnowledgeModal': 'claim-knowledge',
      'chatbot-container': 'chatbot'
    };
    return modalActionMap[modalId];
  }

  // 활성 상태 동기화
  syncActiveState(action) {
    try {
      if (this.activeAction !== action) {
        this.clearActiveAction();

        if (action) {
          const itemElement = document.querySelector(`[data-action="${action}"]`);
          if (itemElement) {
            this.setActiveAction(action, itemElement);
          }
        }
      }
    } catch (error) {
      this.handleError(error, 'syncActiveState');
    }
  }

  /**
   * 기존 FAB/사이드 FAB 비활성화
   * @param {boolean} hasFloating - floating-fab가 있을 때만 사이드 FAB 숨김
   */
  disableLegacyFABs(hasFloating) {
    try {
      const selectors = [
        '#guide-fab',
        '#weekly-fab',
        '#claim-knowledge-fab',
        '#chatbot-fab',
        '.fab-wrap'
      ];

      // floating-fab이 있는 경우에만 .side-actions 숨김 (없으면 절대 숨기지 말 것)
      if (hasFloating) {
        selectors.push('.side-actions');
      }

      selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
          el.style.display = 'none';
          el.setAttribute('aria-hidden', 'true');
        });
      });

      if (this.debugMode) {
        console.log('Legacy FABs disabled (hasFloating=' + !!hasFloating + ')');
      }
    } catch (error) {
      console.warn('Legacy FAB 비활성화 중 오류:', error);
    }
  }

  // 기존 이벤트 리스너와의 충돌 방지
  preventEventConflicts() {
    try {
      // 기존 claim-knowledge 이벤트 제거
      const legacyClaimBtn = document.getElementById('claim-knowledge-fab');
      if (legacyClaimBtn) {
        legacyClaimBtn.replaceWith(legacyClaimBtn.cloneNode(true));
      }
    } catch (error) {
      console.warn('이벤트 충돌 방지 중 오류:', error);
    }
  }

  // 향상된 기능 실행 메서드
  executeActionEnhanced(action) {
    try {
      if (this.debugMode) {
        console.log(`FAB Action executed: ${action}`);
      }

      switch (action) {
        case 'claim-knowledge':
          this.executeClaimKnowledge();
          break;
        case 'guide':
          this.executeGuide();
          break;
        case 'knowhow':
          this.executeKnowhow();
          break;
        case 'chatbot':
          this.executeChatbot();
          break;
        default:
          console.warn(`Unknown action: ${action}`);
      }
    } catch (error) {
      this.handleError(error, 'executeActionEnhanced');
    }
  }

  /** 자동차 보상상식 */
  executeClaimKnowledge() {
    try {
      if (typeof window.openClaimKnowledge === 'function') {
        window.openClaimKnowledge(); // 데이터 로딩 + 모달 표시
        return;
      }
      // 폴백: Bootstrap 모달 직접 열기
      const modal = document.getElementById('claimKnowledgeModal');
      if (modal && typeof bootstrap !== 'undefined') {
        const m = bootstrap.Modal.getOrCreateInstance(modal);
        m.show();
      } else {
        console.warn('claimKnowledgeModal을 찾을 수 없습니다.');
      }
    } catch (error) {
      this.handleError(error, 'executeClaimKnowledge');
    }
  }

  /** 사고처리 가이드 */
  executeGuide() {
    try {
      if (typeof window.openGuide === 'function') {
        window.openGuide();
        return;
      }
      const guideModal = document.getElementById('guideModal');
      if (guideModal && typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getOrCreateInstance(guideModal);
        modal.show();
      } else {
        const legacyBtn = document.getElementById('guide-fab');
        if (legacyBtn && typeof legacyBtn.click === 'function') legacyBtn.click();
        else console.warn('가이드 모달을 열 수 없습니다.');
      }
    } catch (error) {
      this.handleError(error, 'executeGuide');
    }
  }

  /** 자동차 보험상식 */
  executeKnowhow() {
    try {
      if (typeof window.openKnowhow === 'function') {
        window.openKnowhow();
        return;
      }
      const el = document.getElementById('knowhowModal');
      if (el && typeof bootstrap !== 'undefined') {
        const modal = bootstrap.Modal.getOrCreateInstance(el);
        modal.show();
      } else {
        console.warn('knowhowModal을 찾을 수 없습니다.');
      }
    } catch (e) {
      this.handleError(e, 'executeKnowhow');
    }
  }

  /** 챗봇 */
  executeChatbot() {
    try {
      const chatbotContainer = document.getElementById('chatbot-container');
      if (chatbotContainer) {
        chatbotContainer.style.display = 'block';
        chatbotContainer.style.right = '0';
        chatbotContainer.style.transform = 'translateX(0)';
      } else {
        // 폴백: 기존 버튼 트리거
        const legacyBtn = document.getElementById('chatbot-fab');
        if (legacyBtn && typeof legacyBtn.click === 'function') {
          legacyBtn.click();
        } else {
          console.warn('챗봇을 열 수 없습니다.');
        }
      }
    } catch (error) {
      this.handleError(error, 'executeChatbot');
    }
  }

  // 에러 처리 및 복구
  handleError(error, context) {
    console.error(`FAB Controller Error in ${context}:`, error);

    // 상태 초기화
    this.isExpanded = false;
    this.fabContainer?.classList.remove('expanded');
    this.clearActiveAction();

    // 사용자 알림(선택)
    this.announceToScreenReader('일시적인 오류가 발생했습니다. 다시 시도해 주세요.');
  }

  // 디버그 모드
  enableDebugMode() {
    this.debugMode = true;
    console.log('FAB Debug Mode Enabled');

    // 상태 변화 로깅
    const originalSetActiveAction = this.setActiveAction.bind(this);
    this.setActiveAction = function (action, itemElement) {
      console.log(`Setting active action: ${action}`);
      return originalSetActiveAction(action, itemElement);
    };
  }

  // 접근성: 스크린 리더 알림
  announceToScreenReader(message) {
    try {
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', 'polite');
      announcement.setAttribute('aria-atomic', 'true');
      announcement.style.position = 'absolute';
      announcement.style.left = '-10000px';
      announcement.style.width = '1px';
      announcement.style.height = '1px';
      announcement.style.overflow = 'hidden';
      announcement.textContent = message;

      document.body.appendChild(announcement);

      setTimeout(() => {
        document.body.removeChild(announcement);
      }, 1000);
    } catch (error) {
      console.warn('스크린 리더 알림 중 오류:', error);
    }
  }
}

// DOM 로드 후 초기화
document.addEventListener('DOMContentLoaded', () => {
  new FloatingFABController();
});
