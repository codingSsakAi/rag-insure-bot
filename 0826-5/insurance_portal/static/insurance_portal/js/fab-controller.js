/**
 * 플로팅 액션 버튼 컨트롤러 (weekly 대응 완전판)
 * - 스크롤 추적, 확장/수축, 상태 관리
 * - floating-fab이 있으면 레거시 FAB/사이드 버튼 숨김(중복 방지)
 * - floating-fab이 없으면 사이드 버튼(#*-fab)로 폴백
 * - 아이콘 폰트 실패 시 인라인 아이콘 폴백
 * - guide / knowhow / weekly / claim-knowledge / chatbot 실행 & 상태 동기화
 */

class FloatingFABController {
  constructor() {
    // DOM refs
    this.fabContainer = null;
    this.mainToggle = null;
    this.subContainer = null;
    this.actionItems = [];

    // states
    this.isExpanded = false;
    this.activeAction = null;
    this.scrollTimeout = null;
    this.lastScrollY = window.scrollY;
    this.debugMode = false;

    // 메서드 바인딩(폴백 바인딩에서 this 유지)
    this.executeClaimKnowledge = this.executeClaimKnowledge.bind(this);
    this.executeGuide = this.executeGuide.bind(this);
    this.executeKnowhow = this.executeKnowhow.bind(this);
    this.executeWeekly = this.executeWeekly.bind(this);
    this.executeChatbot = this.executeChatbot.bind(this);

    this.init();
  }

  /** 레거시 포털 햄버거(엄격 로더가 만든 #ip-*) 강제 숨김 */
  hideLegacyHamburger() {
    ['ip-fab', 'ip-panel', 'ip-overlay'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.style.setProperty('display', 'none', 'important');
        el.style.setProperty('visibility', 'hidden', 'important');
        el.setAttribute('aria-hidden', 'true');
      }
    });
  }

  /** floating-fab이 없을 때 사이드 버튼을 안전하게 폴백 바인딩 */
  bindSideFallback() {
    const bind = (id, fn) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('click', (e) => {
        e.preventDefault?.();
        fn();
      }, { passive: true });
    };
    bind('claim-knowledge-fab', this.executeClaimKnowledge);
    bind('guide-fab', this.executeGuide);
    bind('weekly-fab', this.executeWeekly);     // ✅ weekly 전용 연결
    bind('chatbot-fab', this.executeChatbot);

    this.ensureIconVisibility();
    if (this.debugMode) console.log('[FAB] 사이드 FAB 폴백 바인딩 완료');
  }

  /** 아이콘 폰트 실패 시 인라인 아이콘/문자 폴백 주입 */
  ensureIconVisibility() {
    try {
      // 메인 토글
      if (this.mainToggle) {
        const hasIcon = !!this.mainToggle.querySelector(
          '.icon-ms, .fa, .fas, .fab, .far, .fa-solid, .material-symbols-outlined, svg'
        );
        if (!hasIcon) {
          const span = document.createElement('span');
          span.textContent = '+';
          span.setAttribute('aria-hidden', 'true');
          span.style.fontSize = '20px';
          span.style.lineHeight = '1';
          this.mainToggle.appendChild(span);
        }
      }
      // 서브 버튼들
      document.querySelectorAll('.fab-sub-btn').forEach(btn => {
        const has = !!btn.querySelector(
          '.icon-ms, .fa, .fas, .fab, .far, .fa-solid, .material-symbols-outlined, svg'
        );
        if (!has) {
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

  /** 기존(레거시) FAB/사이드 액션 숨김: floating-fab 있을 때만 */
  disableLegacyFABs(hasFloatingFab) {
    try {
      const legacySelectors = [
        '#guide-fab',
        '#weekly-fab',
        '#claim-knowledge-fab',
        '#chatbot-fab',
        '.fab-wrap',
        '.side-actions',
      ];
      if (!hasFloatingFab) {
        // floating-fab이 없으면 사이드 버튼 유지(폴백용)
        return;
      }
      legacySelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
          el.style.display = 'none';
          el.setAttribute('aria-hidden', 'true');
        });
      });
      if (this.debugMode) console.log('[FAB] 레거시 FAB/사이드 액션 숨김');
    } catch (e) {
      console.warn('Legacy FAB 비활성화 중 오류:', e);
    }
  }

  /** 기존 이벤트 충돌 방지 (특히 claim-knowledge 등) */
  preventEventConflicts() {
    try {
      const legacyClaimBtn = document.getElementById('claim-knowledge-fab');
      if (legacyClaimBtn) {
        legacyClaimBtn.replaceWith(legacyClaimBtn.cloneNode(true));
      }
      const legacyWeeklyBtn = document.getElementById('weekly-fab');
      if (legacyWeeklyBtn) {
        legacyWeeklyBtn.replaceWith(legacyWeeklyBtn.cloneNode(true));
      }
    } catch (e) {
      console.warn('이벤트 충돌 방지 중 오류:', e);
    }
  }

  init() {
    try {
      this.hideLegacyHamburger();

      // DOM 찾기
      this.fabContainer = document.getElementById('floating-fab');
      this.mainToggle = document.getElementById('fab-main-toggle');
      this.subContainer = document.getElementById('fab-sub-actions');
      this.actionItems = document.querySelectorAll('.fab-action-item');

      const hasFloating = !!(this.fabContainer && this.mainToggle);

      // 공통 보호 로직
      this.preventEventConflicts();
      this.initModalStateTracking();

      if (!hasFloating) {
        console.warn('[FAB] floating-fab 없음 → 사이드 버튼 폴백 모드');
        this.bindSideFallback();
        if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
          this.enableDebugMode();
        }
        return;
      }

      // 중복 노출 방지
      this.disableLegacyFABs(true);

      // 기본 초기화
      this.bindEvents();
      this.initScrollTracking();
      this.ensureIconVisibility();

      // 디버그
      if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
        this.enableDebugMode();
      }

      console.log('FloatingFAB Controller 초기화 완료');
    } catch (error) {
      this.handleError(error, 'init');
    }
  }

  bindEvents() {
    try {
      // 메인 토글
      this.mainToggle.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleExpansion();
      });

      // 서브 버튼
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

      // 라벨도 동일 동작
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
        } catch (err) {
          console.warn('외부 클릭 처리 중 오류:', err);
        }
      });

      // ESC 접기
      document.addEventListener('keydown', (e) => {
        try {
          if (e.key === 'Escape' && this.isExpanded) {
            this.collapseActions();
          }
        } catch (err) {
          console.warn('키보드 이벤트 처리 중 오류:', err);
        }
      });
    } catch (error) {
      this.handleError(error, 'bindEvents');
    }
  }

  initScrollTracking() {
    try {
      window.addEventListener('scroll', () => { this.handleScroll(); }, { passive: true });
      window.addEventListener('resize', () => { this.adjustPosition(); });
      this.adjustPosition();
    } catch (error) {
      this.handleError(error, 'initScrollTracking');
    }
  }

  handleScroll() {
    try {
      const currentScrollY = window.scrollY;
      const scrollDelta = currentScrollY - this.lastScrollY;

      this.updateFABPosition(scrollDelta);
      this.lastScrollY = currentScrollY;

      if (this.isExpanded) {
        clearTimeout(this.scrollTimeout);
        this.scrollTimeout = setTimeout(() => {}, 150);
      }
    } catch (error) {
      console.warn('스크롤 처리 중 오류:', error);
    }
  }

  updateFABPosition() {
    try {
      const viewportHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;
      const denom = Math.max(1, documentHeight - viewportHeight);
      const scrollProgress = Math.min(1, Math.max(0, window.scrollY / denom));

      // 30%~70% 범위 이동
      const minPosition = 30, maxPosition = 70;
      const newPosition = minPosition + (scrollProgress * (maxPosition - minPosition));

      this.fabContainer.style.top = `${newPosition}%`;
      this.fabContainer.style.bottom = 'auto';
      this.fabContainer.style.transform = 'translateY(-50%)';
    } catch (error) {
      console.warn('FAB 위치 업데이트 중 오류:', error);
    }
  }

  adjustPosition() {
    try {
      const w = window.innerWidth;
      const h = window.innerHeight;

      this.fabContainer.style.position = 'fixed';
      this.fabContainer.style.display = 'block';
      this.fabContainer.style.visibility = 'visible';
      this.fabContainer.style.right = w < 768 ? '16px' : '24px';
      this.fabContainer.style.top = h < 600 ? '40%' : '50%';
      this.fabContainer.style.transform = 'translateY(-50%)';
    } catch (error) {
      console.warn('위치 조정 중 오류:', error);
    }
  }

  toggleExpansion() {
    try {
      if (this.isExpanded) this.collapseActions();
      else this.expandActions();
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
      document.body.classList.add('fab-backdrop-active');
      this.announceToScreenReader('메뉴가 열렸습니다');
      if (this.debugMode) console.log('FAB 확장됨');
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
      document.body.classList.remove('fab-backdrop-active');
      if (this.activeAction) this.clearActiveAction();
      this.announceToScreenReader('메뉴가 닫혔습니다');
      if (this.debugMode) console.log('FAB 접힘');
    } catch (error) {
      this.handleError(error, 'collapseActions');
    }
  }

  handleActionClick(action, itemElement) {
    try {
      if (this.activeAction) this.clearActiveAction();
      this.setActiveAction(action, itemElement);
      this.executeActionEnhanced(action);
      setTimeout(() => this.collapseActions(), 300);
    } catch (error) {
      this.handleError(error, 'handleActionClick');
    }
  }

  setActiveAction(action, itemElement) {
    try {
      this.activeAction = action;
      itemElement.classList.add('active');
      const button = itemElement.querySelector('.fab-sub-btn');
      if (button) button.setAttribute('aria-pressed', 'true');
      if (this.debugMode) console.log(`Active action: ${action}`);
    } catch (error) {
      this.handleError(error, 'setActiveAction');
    }
  }

  clearActiveAction() {
    try {
      if (!this.activeAction) return;
      const activeItem = document.querySelector(`[data-action="${this.activeAction}"]`);
      if (activeItem) {
        activeItem.classList.remove('active');
        const button = activeItem.querySelector('.fab-sub-btn');
        if (button) button.setAttribute('aria-pressed', 'false');
      }
      if (this.debugMode) console.log(`Active cleared: ${this.activeAction}`);
      this.activeAction = null;
    } catch (error) {
      this.handleError(error, 'clearActiveAction');
    }
  }

  /** 모달/패널 상태 감지 → FAB 항목 active 동기화 (weekly 포함) */
  initModalStateTracking() {
    try {
      // Bootstrap 모달들
      const bsModals = ['guideModal', 'knowhowModal', 'weeklyModal'];
      bsModals.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('shown.bs.modal', () => {
          this.syncActiveState(this.getActionByModalId(id));
        });
        el.addEventListener('hidden.bs.modal', () => {
          this.clearActiveAction();
        });
      });

      // 커스텀 모달 감시(클래스/hidden) : claim-knowledge, knowhow, weekly
      const watchIds = ['claim-knowledge-modal', 'knowhow-modal', 'weekly-modal'];
      watchIds.forEach(mid => {
        const target = document.getElementById(mid);
        if (!target) return;
        const obs = new MutationObserver(muts => {
          muts.forEach(m => {
            if (m.type === 'attributes' && (m.attributeName === 'hidden' || m.attributeName === 'class')) {
              const isShown = !target.hasAttribute('hidden') || target.classList.contains('show');
              if (isShown) this.syncActiveState(this.getActionByModalId(mid));
              else this.clearActiveAction();
            }
          });
        });
        obs.observe(target, { attributes: true, attributeFilter: ['hidden', 'class'] });
      });

      // 챗봇 패널
      const chatbotContainer = document.getElementById('chatbot-container');
      if (chatbotContainer) {
        const chatbotObserver = new MutationObserver((muts) => {
          muts.forEach(m => {
            if (m.type === 'attributes' && m.attributeName === 'style') {
              const display = window.getComputedStyle(chatbotContainer).display;
              if (display !== 'none') this.syncActiveState('chatbot');
              else this.clearActiveAction();
            }
          });
        });
        chatbotObserver.observe(chatbotContainer, { attributes: true, attributeFilter: ['style'] });
      }
    } catch (error) {
      this.handleError(error, 'initModalStateTracking');
    }
  }

  /** 모달 ID → 액션 매핑 */
  getActionByModalId(modalId) {
    const map = {
      'guideModal': 'guide',
      'knowhowModal': 'knowhow',
      'knowhow-modal': 'knowhow',
      'weeklyModal': 'weekly',          // ✅ 부트스트랩 weekly
      'weekly-modal': 'weekly',         // ✅ 커스텀 weekly
      'claim-knowledge-modal': 'claim-knowledge',
      'chatbot-container': 'chatbot'
    };
    return map[modalId];
  }

  /** 현재 열린 UI와 FAB active 상태 동기화 */
  syncActiveState(action) {
    try {
      if (!action || this.activeAction === action) return;
      this.clearActiveAction();
      const item = document.querySelector(`[data-action="${action}"]`);
      if (item) this.setActiveAction(action, item);
    } catch (error) {
      this.handleError(error, 'syncActiveState');
    }
  }

  /** 액션 실행 디스패처 */
  executeActionEnhanced(action) {
    try {
      if (this.debugMode) console.log(`Execute: ${action}`);
      switch (action) {
        case 'claim-knowledge': return this.executeClaimKnowledge();
        case 'guide':           return this.executeGuide();
        case 'knowhow':         return this.executeKnowhow();
        case 'weekly':          return this.executeWeekly();   // ✅ weekly 실행
        case 'chatbot':         return this.executeChatbot();
        default:
          console.warn(`Unknown action: ${action}`);
      }
    } catch (error) {
      this.handleError(error, 'executeActionEnhanced');
    }
  }

  // ====== 각 액션 구체 동작 ======

  executeClaimKnowledge() {
    try {
      if (typeof window.openClaimKnowledge === 'function') {
        window.openClaimKnowledge(); // 데이터 로딩 + 모달
        return;
      }
      const modal = document.getElementById('claim-knowledge-modal');
      if (modal) {
        modal.removeAttribute('hidden');
        requestAnimationFrame(() => modal.classList.add('show'));
      } else {
        console.warn('claim-knowledge-modal을 찾을 수 없습니다.');
      }
    } catch (e) {
      this.handleError(e, 'executeClaimKnowledge');
    }
  }

  executeGuide() {
    try {
      if (typeof window.openGuide === 'function') {
        window.openGuide();
        return;
      }
      const guideModal = document.getElementById('guideModal');
      if (guideModal && typeof bootstrap !== 'undefined' && typeof bootstrap.Modal === 'function') {
        new bootstrap.Modal(guideModal).show();
      } else {
        const legacyBtn = document.getElementById('guide-fab');
        if (legacyBtn && typeof legacyBtn.click === 'function') legacyBtn.click();
        else console.warn('가이드 모달을 열 수 없습니다.');
      }
    } catch (e) {
      this.handleError(e, 'executeGuide');
    }
  }

  executeKnowhow() {
    try {
      if (typeof window.openKnowhow === 'function') {
        window.openKnowhow();
        return;
      }
      // 커스텀 모달 우선
      const custom = document.getElementById('knowhow-modal');
      if (custom) {
        custom.removeAttribute('hidden');
        requestAnimationFrame(() => custom.classList.add('show'));
        return;
      }
      // 부트스트랩 모달
      const bs = document.getElementById('knowhowModal');
      if (bs && typeof bootstrap !== 'undefined' && typeof bootstrap.Modal === 'function') {
        new bootstrap.Modal(bs).show();
        return;
      }
      // 폴백: 레거시 버튼
      const legacyBtn = document.getElementById('knowhow-fab') || document.getElementById('weekly-fab');
      if (legacyBtn && typeof legacyBtn.click === 'function') legacyBtn.click();
      else console.warn('노하우/주간 모달을 열 수 없습니다.');
    } catch (e) {
      this.handleError(e, 'executeKnowhow');
    }
  }

  /** ✅ weekly 전용 실행 로직 (다층 폴백) */
  executeWeekly() {
    try {
      // 1) 전역 오프너
      if (typeof window.openWeekly === 'function') {
        window.openWeekly();
        return;
      }
      // 2) 커스텀 모달(#weekly-modal)
      const custom = document.getElementById('weekly-modal');
      if (custom) {
        custom.removeAttribute('hidden');
        requestAnimationFrame(() => custom.classList.add('show'));
        return;
      }
      // 3) 부트스트랩 모달(#weeklyModal)
      const bs = document.getElementById('weeklyModal');
      if (bs && typeof bootstrap !== 'undefined' && typeof bootstrap.Modal === 'function') {
        new bootstrap.Modal(bs).show();
        return;
      }
      // 4) 레거시 버튼 트리거
      const legacyBtn = document.getElementById('weekly-fab') || document.getElementById('knowhow-fab');
      if (legacyBtn && typeof legacyBtn.click === 'function') {
        legacyBtn.click();
        return;
      }
      console.warn('weekly UI를 열 수 없습니다.');
    } catch (e) {
      this.handleError(e, 'executeWeekly');
    }
  }

  executeChatbot() {
    try {
      const container = document.getElementById('chatbot-container');
      if (container) {
        container.style.display = 'block';
        container.style.right = '0';
        container.style.transform = 'translateX(0)';
      } else {
        const legacyBtn = document.getElementById('chatbot-fab');
        if (legacyBtn && typeof legacyBtn.click === 'function') legacyBtn.click();
        else console.warn('챗봇을 열 수 없습니다.');
      }
    } catch (e) {
      this.handleError(e, 'executeChatbot');
    }
  }

  // ====== 에러/디버그/접근성 ======

  handleError(error, context) {
    console.error(`FAB Controller Error in ${context}:`, error);
    this.isExpanded = false;
    this.fabContainer?.classList.remove('expanded');
    this.clearActiveAction();
    this.announceToScreenReader('일시적인 오류가 발생했습니다. 다시 시도해 주세요.');
  }

  enableDebugMode() {
    this.debugMode = true;
    console.log('FAB Debug Mode Enabled');
    const orig = this.setActiveAction.bind(this);
    this.setActiveAction = (action, el) => {
      console.log(`Setting active action: ${action}`);
      return orig(action, el);
    };
  }

  announceToScreenReader(message) {
    try {
      const el = document.createElement('div');
      el.setAttribute('aria-live', 'polite');
      el.setAttribute('aria-atomic', 'true');
      el.style.position = 'absolute';
      el.style.left = '-10000px';
      el.style.width = '1px';
      el.style.height = '1px';
      el.style.overflow = 'hidden';
      el.textContent = message;
      document.body.appendChild(el);
      setTimeout(() => { document.body.removeChild(el); }, 1000);
    } catch (e) {
      console.warn('스크린 리더 알림 중 오류:', e);
    }
  }
}

// DOM 로드 후 초기화
document.addEventListener('DOMContentLoaded', () => {
  new FloatingFABController();
});
