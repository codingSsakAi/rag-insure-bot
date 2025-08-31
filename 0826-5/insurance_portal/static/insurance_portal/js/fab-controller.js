/**
 * 플로팅 액션 버튼 컨트롤러
 * 스크롤 추적, 확장/수축, 상태 관리
 * 
 * 변경 요약(최소 변경):
 * - ensureFabCss(): 아카이브 CSS 자동 로드
 * - ensureFabMarkup(): #floating-fab 마크업 없을 때 자동 생성(기존 구조/ID 유지)
 * - hideHamburger(): 3선 토글(UI/이벤트) 완전 비표시 + MutationObserver 보강
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
    
    this.init();
  }

  // [추가] 아카이브 CSS 보장
  ensureFabCss() {
    try {
      const href = "/0826-5/insurance_portal/static/insurance_portal/css/fab.css";
      if (!document.querySelector(`link[href*="${href}"]`)) {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = href;
        document.head.appendChild(link);
      }
      // 선택: 햄버거 차단 보루 CSS(있으면 로드)
      const killHref = "/0826-5/insurance_portal/static/insurance_portal/css/hamburger-off.css";
      if (window.__LOAD_HAMBURGER_OFF_CSS__ && !document.querySelector(`link[href*="${killHref}"]`)) {
        const link2 = document.createElement("link");
        link2.rel = "stylesheet";
        link2.href = killHref;
        document.head.appendChild(link2);
      }
    } catch (_) {}
  }

  // [추가] FAB 마크업 보장(없으면 생성) – 기존 ID/클래스 그대로 사용
  ensureFabMarkup() {
    try {
      if (document.getElementById('floating-fab')) return; // 이미 있으면 그대로 사용

      const container = document.createElement('div');
      container.id = 'floating-fab';
      container.className = 'floating-fab';
      container.innerHTML = `
        <button id="fab-main-toggle" class="fab-main-toggle" aria-label="메뉴 열기" aria-expanded="false">+</button>
        <ul id="fab-sub-actions" class="fab-sub-actions" aria-hidden="true">
          <li class="fab-action-item" data-action="guide">
            <button class="fab-sub-btn" type="button" aria-pressed="false">가이드</button>
            <span class="fab-label">사고 가이드</span>
          </li>
          <li class="fab-action-item" data-action="knowhow">
            <button class="fab-sub-btn" type="button" aria-pressed="false">상식</button>
            <span class="fab-label">보험 상식</span>
          </li>
          <li class="fab-action-item" data-action="claim-knowledge">
            <button class="fab-sub-btn" type="button" aria-pressed="false">보상</button>
            <span class="fab-label">보상 상식</span>
          </li>
          <li class="fab-action-item" data-action="chatbot">
            <button class="fab-sub-btn" type="button" aria-pressed="false">챗봇</button>
            <span class="fab-label">과실 챗봇</span>
          </li>
        </ul>
      `;
      // body 보장 후 삽입
      if (!document.body) {
        document.addEventListener('DOMContentLoaded', () => document.body.appendChild(container));
      } else {
        document.body.appendChild(container);
      }
    } catch (_) {}
  }

  // [추가] 3선 토글 완전 제거(표시/이벤트 모두) + 동적 삽입 대응
  hideHamburger() {
    const KILL_STYLE_ID = "hamburger-off-style";
    if (!document.getElementById(KILL_STYLE_ID)) {
      const st = document.createElement("style");
      st.id = KILL_STYLE_ID;
      st.textContent = `
        .hamburger, .hamburger-menu, .menu-toggle, .nav-drawer,
        #hamburger, #menuToggle, #navDrawer {
          display: none !important;
          visibility: hidden !important;
          pointer-events: none !important;
          opacity: 0 !important;
          width: 0 !important; height: 0 !important;
          position: absolute !important; left: -99999px !important; top: -99999px !important;
        }
      `;
      document.head.appendChild(st);
    }

    const killOnce = () => {
      const selectors = [
        ".hamburger", ".hamburger-menu", ".menu-toggle", ".nav-drawer",
        "#hamburger", "#menuToggle", "#navDrawer"
      ];
      document.querySelectorAll(selectors.join(",")).forEach(el => {
        try {
          el.style.display = "none";
          el.style.visibility = "hidden";
          el.style.pointerEvents = "none";
          el.setAttribute("aria-hidden", "true");
          const clone = el.cloneNode(true);
          el.parentNode && el.parentNode.replaceChild(clone, el);
        } catch (_) {}
      });
      document.body && document.body.classList.remove("drawer-open","menu-open","nav-open","is-open","open");
    };

    killOnce();

    if (!window.__HAMBURGER_OBSERVING__) {
      window.__HAMBURGER_OBSERVING__ = true;
      const mo = new MutationObserver(muts => {
        let found = false;
        for (const m of muts) {
          if (m.addedNodes && m.addedNodes.length) {
            for (const n of m.addedNodes) {
              if (!(n instanceof Element)) continue;
              if (
                n.matches?.(".hamburger, .hamburger-menu, .menu-toggle, .nav-drawer, #hamburger, #menuToggle, #navDrawer") ||
                n.querySelector?.(".hamburger, .hamburger-menu, .menu-toggle, .nav-drawer, #hamburger, #menuToggle, #navDrawer")
              ) { found = true; break; }
            }
          }
          if (found) break;
        }
        if (found) killOnce();
      });
      mo.observe(document.documentElement, { childList: true, subtree: true });
    }
  }

  init() {
    try {
      // [추가] CSS/마크업/햄버거 제거 보장
      this.ensureFabCss();
      this.ensureFabMarkup();
      this.hideHamburger();

      // DOM 요소 찾기
      this.fabContainer = document.getElementById('floating-fab');
      this.mainToggle = document.getElementById('fab-main-toggle');
      this.subContainer = document.getElementById('fab-sub-actions');
      this.actionItems = document.querySelectorAll('.fab-action-item');

      if (!this.fabContainer || !this.mainToggle) {
        console.warn('FAB 요소를 찾을 수 없습니다.');
        return;
      }

      // 새로운 초기화 코드들
      this.disableLegacyFABs();
      this.preventEventConflicts();
      this.initModalStateTracking();
      
      // 기본 초기화
      this.bindEvents();
      this.initScrollTracking();
      
      // 디버그 모드 (개발 시에만)
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
          // 스크롤이 멈춘 후 잠시 대기
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
      const scrollProgress = window.scrollY / (documentHeight - viewportHeight);
      
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
      // 뷰포트 크기에 따른 위치 조정
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
    
      // 초기 위치 강제 설정
      this.fabContainer.style.position = 'fixed';
      this.fabContainer.style.display = 'block';
      this.fabContainer.style.visibility = 'visible';
      
      if (viewportWidth < 768) {
        this.fabContainer.style.right = '16px';
      } else {
        this.fabContainer.style.right = '24px';
      }

      // 초기에는 중앙 고정
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

      // 추가: 백드롭 표시
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

      // 추가: 백드롭 제거
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
      const bootstrapModals = ['guideModal', 'knowhowModal'];
      
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

      // 커스텀 모달 감지 (claim-knowledge)
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'attributes' && mutation.attributeName === 'hidden') {
            const target = mutation.target;
            if (target.id === 'claim-knowledge-modal') {
              if (!target.hasAttribute('hidden')) {
                this.syncActiveState('claim-knowledge');
              } else {
                this.clearActiveAction();
              }
            }
          }
          
          if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            const target = mutation.target;
            if (target.id === 'claim-knowledge-modal' && target.classList.contains('show')) {
              this.syncActiveState('claim-knowledge');
            }
          }
        });
      });

      const claimModal = document.getElementById('claim-knowledge-modal');
      if (claimModal) {
        observer.observe(claimModal, { 
          attributes: true, 
          attributeFilter: ['hidden', 'class'] 
        });
      }

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
      'claim-knowledge-modal': 'claim-knowledge',
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

  // 기존 FAB 버튼들 비활성화
  disableLegacyFABs() {
    try {
      const legacySelectors = [
        '#guide-fab',
        '#weekly-fab', 
        '#claim-knowledge-fab',
        '#chatbot-fab',
        '.fab-wrap',
        '.side-actions'
      ];

      legacySelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
          el.style.display = 'none';
          el.setAttribute('aria-hidden', 'true');
        });
      });

      if (this.debugMode) {
        console.log('Legacy FABs disabled');
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
      // 액션 실행 로깅
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

  executeClaimKnowledge() {
    try {
      if (typeof window.openClaimKnowledge === "function") {
        window.openClaimKnowledge();   // 데이터 로딩 + 모달 표시
        return;
      }
      // 폴백: 모달만 표시
      const modal = document.getElementById('claim-knowledge-modal');
      if (modal) {
        modal.removeAttribute('hidden');
        requestAnimationFrame(() => {
          modal.classList.add('show');
        });
      } else {
        console.warn('claim-knowledge-modal을 찾을 수 없습니다.');
      }
    } catch (error) {
      this.handleError(error, 'executeClaimKnowledge');
    }
  }

  executeGuide() {
    try {
        // 전역 오프너가 있으면 데이터 로딩+모달 표시를 한 번에
        if (typeof window.openGuide === 'function') {
        window.openGuide();
        return;
        }
        // 폴백: 기존 버튼 클릭 또는 단순 모달 show
        const guideModal = document.getElementById('guideModal');
        if (guideModal && typeof bootstrap !== 'undefined') {
        const modal = new bootstrap.Modal(guideModal);
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

  executeKnowhow() {
    try {
        // 권장: 전역 오프너 사용
        if (typeof window.openKnowhow === 'function') {
        window.openKnowhow();
        return;
        }
        // 폴백: 직접 모달 표시 (커스텀 모달)
        const el = document.getElementById('knowhow-modal'); // <-- 하이픈 ID
        if (el) {
        el.removeAttribute('hidden');
        requestAnimationFrame(() => el.classList.add('show'));
        } else {
        console.warn('knowhow-modal을 찾을 수 없습니다.');
        }
    } catch (e) {
        this.handleError(e, 'executeKnowhow');
    }
  }

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
    
    // 사용자에게 알림 (선택적)
    this.announceToScreenReader('일시적인 오류가 발생했습니다. 다시 시도해 주세요.');
  }

  // 디버그 모드
  enableDebugMode() {
    this.debugMode = true;
    console.log('FAB Debug Mode Enabled');
    
    // 상태 변화 로깅
    const originalSetActiveAction = this.setActiveAction;
    this.setActiveAction = function(action, itemElement) {
      console.log(`Setting active action: ${action}`);
      return originalSetActiveAction.call(this, action, itemElement);
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
