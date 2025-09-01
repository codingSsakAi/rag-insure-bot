/**
 * 플로팅 액션 버튼 컨트롤러 (weekly 고장 복구 + 동적 바인딩 강화판)
 * - floating-fab 있으면 레거시 사이드 FAB 숨김, 없으면 폴백 바인딩
 * - weekly/knowhow/guide/claim-knowledge/chatbot 실행
 * - 동적으로 늦게 로드되는 FAB/모달을 MutationObserver로 감시하여 자동 바인딩
 * - 아이콘 폰트 실패 시 인라인 아이콘 폴백
 * - 디버그 모드: localhost, URL에 ?fabdebug=1, 또는 localStorage.fab.debug="1" 이면 활성
 */

(function () {
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
      this.ready = false;

      // public openers(없을 때만 정의 → 파일 추가 없이 사용)
      this.ensureGlobalOpeners();

      // 초기 디버그 모드 설정
      this.debugMode = this.isDebugEnabled();

      // 즉시 시도 + 동적 대기
      this.trySetupNow();
      this.waitForFABAppear();
      this.watchLateModals();
    }

    log(...a) { if (this.debugMode) console.log('[FAB]', ...a); }
    warn(...a) { if (this.debugMode) console.warn('[FAB]', ...a); }

    isDebugEnabled() {
      try {
        if (location.search.includes('fabdebug=1')) return true;
        const ls = (localStorage.getItem('fab.debug') || '').trim();
        if (ls === '1' || ls.toLowerCase() === 'true') return true;
        if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') return true;
      } catch (_) {}
      return false;
    }

    /** 전역 오프너가 없으면 간단 구현(데이터 로딩은 기존 함수가 있으면 그걸 우선 사용) */
    ensureGlobalOpeners() {
      if (typeof window.openWeekly !== 'function') {
        window.openWeekly = () => {
          // 1) 커스텀 모달
          const c = document.getElementById('weekly-modal');
          if (c) {
            c.removeAttribute('hidden');
            requestAnimationFrame(() => c.classList.add('show'));
            this.log('openWeekly: custom modal #weekly-modal');
            return true;
          }
          // 2) 부트스트랩 모달
          const b = document.getElementById('weeklyModal');
          if (b && typeof window.bootstrap !== 'undefined' && typeof window.bootstrap.Modal === 'function') {
            new window.bootstrap.Modal(b).show();
            this.log('openWeekly: bootstrap modal #weeklyModal');
            return true;
          }
          // 3) 레거시 버튼
          const legacy = document.getElementById('weekly-fab') || document.getElementById('knowhow-fab');
          if (legacy && typeof legacy.click === 'function') {
            legacy.click();
            this.log('openWeekly: legacy button clicked');
            return true;
          }
          // 4) 앵커 자동 탐색
          const a = document.querySelector('a[href*="weekly"], a[href*="주간"]');
          if (a) { a.click(); this.log('openWeekly: anchor clicked'); return true; }

          this.warn('openWeekly: 열 대상 없음');
          return false;
        };
      }
      if (typeof window.openKnowhow !== 'function') {
        window.openKnowhow = () => {
          const c = document.getElementById('knowhow-modal');
          if (c) {
            c.removeAttribute('hidden');
            requestAnimationFrame(() => c.classList.add('show'));
            this.log('openKnowhow: custom modal #knowhow-modal');
            return true;
          }
          const b = document.getElementById('knowhowModal');
          if (b && typeof window.bootstrap !== 'undefined' && typeof window.bootstrap.Modal === 'function') {
            new window.bootstrap.Modal(b).show();
            this.log('openKnowhow: bootstrap modal #knowhowModal');
            return true;
          }
          const legacy = document.getElementById('knowhow-fab');
          if (legacy && typeof legacy.click === 'function') { legacy.click(); this.log('openKnowhow: legacy clicked'); return true; }
          this.warn('openKnowhow: 열 대상 없음');
          return false;
        };
      }
      if (typeof window.openGuide !== 'function') {
        window.openGuide = () => {
          const b = document.getElementById('guideModal');
          if (b && typeof window.bootstrap !== 'undefined' && typeof window.bootstrap.Modal === 'function') {
            new window.bootstrap.Modal(b).show();
            this.log('openGuide: bootstrap modal');
            return true;
          }
          const legacy = document.getElementById('guide-fab');
          if (legacy && typeof legacy.click === 'function') { legacy.click(); this.log('openGuide: legacy clicked'); return true; }
          this.warn('openGuide: 열 대상 없음');
          return false;
        };
      }
      if (typeof window.openClaimKnowledge !== 'function') {
        window.openClaimKnowledge = () => {
          const m = document.getElementById('claim-knowledge-modal');
          if (m) {
            m.removeAttribute('hidden');
            requestAnimationFrame(() => m.classList.add('show'));
            this.log('openClaimKnowledge: custom modal');
            return true;
          }
          const legacy = document.getElementById('claim-knowledge-fab');
          if (legacy && typeof legacy.click === 'function') { legacy.click(); this.log('openClaimKnowledge: legacy clicked'); return true; }
          this.warn('openClaimKnowledge: 열 대상 없음');
          return false;
        };
      }
    }

    /** 한 번 즉시 셋업 시도 */
    trySetupNow() {
      const had = this.setupIfReady();
      this.log('trySetupNow →', had ? 'READY' : 'NOT READY');
    }

    /** #floating-fab 이 늦게 생기는 경우 감시해서 자동 셋업 */
    waitForFABAppear() {
      if (this.ready) return;
      const t0 = Date.now();
      const limitMs = 5000;

      const check = () => {
        if (this.ready) return;
        const ok = this.setupIfReady();
        if (ok) return;
        if (Date.now() - t0 > limitMs) {
          this.log('FAB not found in time → side fallback');
          this.bindSideFallback(); // 폴백으로라도 동작 보장
          return;
        }
        requestAnimationFrame(check);
      };
      requestAnimationFrame(check);
    }

    /** weekly/knowhow 등의 모달이 늦게 로드될 때 active 동기화 */
    watchLateModals() {
      const ids = ['weekly-modal','weeklyModal','knowhow-modal','knowhowModal','guideModal','claim-knowledge-modal','chatbot-container'];
      const obs = new MutationObserver(() => {
        // 모달이 뒤늦게 생기면 이벤트 바인딩/동기화 다시 설정
        this.initModalStateTracking(true);
      });
      obs.observe(document.documentElement, { childList: true, subtree: true });
      // 초기에 한 번
      this.initModalStateTracking(false);
    }

    /** floating-fab 있으면 플로팅 셋업, 없으면 false */
    setupIfReady() {
      try {
        this.fabContainer = document.getElementById('floating-fab');
        this.mainToggle = document.getElementById('fab-main-toggle');
        this.subContainer = document.getElementById('fab-sub-actions');
        this.actionItems = document.querySelectorAll('.fab-action-item');

        const hasFloating = !!(this.fabContainer && this.mainToggle);
        if (!hasFloating) return false;

        this.hideStrictHamburger();
        this.preventEventConflicts();
        this.bindEvents();
        this.initScrollTracking();
        this.ensureIconVisibility();
        this.disableLegacyFABs(true);
        this.ready = true;

        this.log('FloatingFAB Controller 초기화 완료');
        return true;
      } catch (e) {
        this.handleError(e, 'setupIfReady');
        return false;
      }
    }

    /** portal 엄격 로더가 만든 햄버거 흔적 숨김 */
    hideStrictHamburger() {
      ['ip-fab', 'ip-panel', 'ip-overlay'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.style.setProperty('display', 'none', 'important');
          el.style.setProperty('visibility', 'hidden', 'important');
          el.setAttribute('aria-hidden', 'true');
        }
      });
    }

    /** floating-fab 없을 때 사이드 FAB 폴백 바인딩 */
    bindSideFallback() {
      const bind = (id, fn) => {
        const el = document.getElementById(id);
        if (el) {
          el.addEventListener('click', (e) => { e.preventDefault?.(); fn(); }, { passive: true });
          this.log('side fallback bind:', id);
        }
      };
      bind('weekly-fab', () => this.executeWeekly());
      bind('knowhow-fab', () => this.executeKnowhow());
      bind('guide-fab', () => this.executeGuide());
      bind('claim-knowledge-fab', () => this.executeClaimKnowledge());
      bind('chatbot-fab', () => this.executeChatbot());
      this.ensureIconVisibility();
    }

    /** 레거시 FAB/사이드 버튼 숨김 (floating-fab 있을 때만) */
    disableLegacyFABs(hasFloatingFab) {
      if (!hasFloatingFab) return;
      ['#guide-fab','#weekly-fab','#knowhow-fab','#claim-knowledge-fab','#chatbot-fab','.fab-wrap','.side-actions'].forEach(sel=>{
        document.querySelectorAll(sel).forEach(el=>{
          el.style.display = 'none';
          el.setAttribute('aria-hidden','true');
        });
      });
    }

    /** 기존 이벤트 충돌 방지 */
    preventEventConflicts() {
      ['claim-knowledge-fab','weekly-fab','knowhow-fab','guide-fab','chatbot-fab'].forEach(id=>{
        const el = document.getElementById(id);
        if (el) el.replaceWith(el.cloneNode(true));
      });
    }

    /** 아이콘 폰트 실패 시 폴백 */
    ensureIconVisibility() {
      try {
        // 메인 토글
        if (this.mainToggle) {
          const has = !!this.mainToggle.querySelector('.icon-ms, .fa, .fas, .fab, .far, .fa-solid, .material-symbols-outlined, svg');
          if (!has) {
            const span = document.createElement('span');
            span.textContent = '+';
            span.setAttribute('aria-hidden','true');
            span.style.fontSize='20px'; span.style.lineHeight='1';
            this.mainToggle.appendChild(span);
          }
        }
        // 서브 버튼
        document.querySelectorAll('.fab-sub-btn').forEach(btn=>{
          const has = !!btn.querySelector('.icon-ms, .fa, .fas, .fab, .far, .fa-solid, .material-symbols-outlined, svg');
          if (!has) {
            const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
            svg.setAttribute('viewBox','0 0 24 24');
            svg.style.width='20px'; svg.style.height='20px';
            svg.setAttribute('aria-hidden','true');
            const c = document.createElementNS('http://www.w3.org/2000/svg','circle');
            c.setAttribute('cx','12'); c.setAttribute('cy','12'); c.setAttribute('r','5'); c.setAttribute('fill','currentColor');
            svg.appendChild(c);
            btn.prepend(svg);
          }
        });
      } catch (e) { this.warn('아이콘 폴백 주입 오류', e); }
    }

    bindEvents() {
      try {
        // 메인 토글
        this.mainToggle.addEventListener('click', (e) => { e.preventDefault(); this.toggleExpansion(); });

        // 서브 버튼 + 라벨: 액션 디스패치
        const hookup = (el) => {
          const actionRaw = el.dataset.action || '';
          const action = this.normalizeAction(actionRaw);
          const btn = el.querySelector('.fab-sub-btn');
          const label = el.querySelector('.fab-label');
          const handler = (e) => { e.preventDefault(); this.handleActionClick(action, el); };
          if (btn) btn.addEventListener('click', handler);
          if (label) label.addEventListener('click', handler);
        };
        this.actionItems.forEach(hookup);

        // 외부 클릭 접기
        document.addEventListener('click', (e) => {
          try {
            if (this.fabContainer && !this.fabContainer.contains(e.target) && this.isExpanded) this.collapseActions();
          } catch (err) { this.warn('외부 클릭 처리 오류', err); }
        });

        // ESC 접기
        document.addEventListener('keydown', (e) => {
          try { if (e.key === 'Escape' && this.isExpanded) this.collapseActions(); }
          catch (err) { this.warn('키보드 처리 오류', err); }
        });

        // 스크롤/리사이즈
        this.initScrollTracking();

        // 모달 상태 추적
        this.initModalStateTracking(false);

        this.log('bindEvents done');
      } catch (e) {
        this.handleError(e, 'bindEvents');
      }
    }

    /** 액션 명 정규화: weekly/knowhow/주간 등 다양한 data-action/text 대응 */
    normalizeAction(a) {
      const s = (a || '').toLowerCase();
      if (!s) return '';
      if (s.includes('weekly') || s.includes('주간') || s.includes('week')) return 'weekly';
      if (s.includes('knowhow') || s.includes('노하우')) return 'knowhow';
      return s;
    }

    initScrollTracking() {
      try {
        window.addEventListener('scroll', () => this.handleScroll(), { passive: true });
        window.addEventListener('resize', () => this.adjustPosition());
        this.adjustPosition();
      } catch (e) { this.handleError(e, 'initScrollTracking'); }
    }

    handleScroll() {
      try {
        const cur = window.scrollY;
        const delta = cur - this.lastScrollY;
        this.updateFABPosition(delta);
        this.lastScrollY = cur;
        if (this.isExpanded) {
          clearTimeout(this.scrollTimeout);
          this.scrollTimeout = setTimeout(()=>{}, 150);
        }
      } catch (e) { this.warn('스크롤 처리 오류', e); }
    }

    updateFABPosition() {
      try {
        if (!this.fabContainer) return;
        const vh = window.innerHeight;
        const dh = document.documentElement.scrollHeight;
        const denom = Math.max(1, dh - vh);
        const prog = Math.min(1, Math.max(0, window.scrollY / denom));
        const min = 30, max = 70;
        const pos = min + (prog * (max - min));
        this.fabContainer.style.top = `${pos}%`;
        this.fabContainer.style.bottom = 'auto';
        this.fabContainer.style.transform = 'translateY(-50%)';
      } catch (e) { this.warn('FAB 위치 업데이트 오류', e); }
    }

    adjustPosition() {
      try {
        if (!this.fabContainer) return;
        const w = window.innerWidth, h = window.innerHeight;
        this.fabContainer.style.position = 'fixed';
        this.fabContainer.style.display = 'block';
        this.fabContainer.style.visibility = 'visible';
        this.fabContainer.style.right = w < 768 ? '16px' : '24px';
        this.fabContainer.style.top = h < 600 ? '40%' : '50%';
        this.fabContainer.style.transform = 'translateY(-50%)';
      } catch (e) { this.warn('위치 조정 오류', e); }
    }

    toggleExpansion() { try { this.isExpanded ? this.collapseActions() : this.expandActions(); } catch (e) { this.handleError(e, 'toggleExpansion'); } }

    expandActions() {
      try {
        this.isExpanded = true;
        this.fabContainer.classList.add('expanded');
        this.mainToggle.setAttribute('aria-label','메뉴 닫기');
        this.mainToggle.setAttribute('aria-expanded','true');
        document.body.classList.add('fab-backdrop-active');
        this.announce('메뉴가 열렸습니다');
        this.log('expanded');
      } catch (e) { this.handleError(e, 'expandActions'); }
    }

    collapseActions() {
      try {
        this.isExpanded = false;
        this.fabContainer.classList.remove('expanded');
        this.mainToggle.setAttribute('aria-label','메뉴 열기');
        this.mainToggle.setAttribute('aria-expanded','false');
        document.body.classList.remove('fab-backdrop-active');
        if (this.activeAction) this.clearActiveAction();
        this.announce('메뉴가 닫혔습니다');
        this.log('collapsed');
      } catch (e) { this.handleError(e, 'collapseActions'); }
    }

    handleActionClick(action, itemEl) {
      try {
        if (!action) return;
        if (this.activeAction) this.clearActiveAction();
        this.setActiveAction(action, itemEl);
        this.executeAction(action);
        setTimeout(() => this.collapseActions(), 300);
      } catch (e) { this.handleError(e, 'handleActionClick'); }
    }

    setActiveAction(action, itemEl) {
      try {
        this.activeAction = action;
        if (itemEl) {
          itemEl.classList.add('active');
          const btn = itemEl.querySelector('.fab-sub-btn');
          if (btn) btn.setAttribute('aria-pressed','true');
        }
        this.log('active:', action);
      } catch (e) { this.handleError(e, 'setActiveAction'); }
    }

    clearActiveAction() {
      try {
        if (!this.activeAction) return;
        const el = document.querySelector(`[data-action="${this.activeAction}"]`);
        if (el) {
          el.classList.remove('active');
          const btn = el.querySelector('.fab-sub-btn');
          if (btn) btn.setAttribute('aria-pressed','false');
        }
        this.log('active cleared:', this.activeAction);
        this.activeAction = null;
      } catch (e) { this.handleError(e, 'clearActiveAction'); }
    }

    /** 모달/패널 상태 추적(weekly 포함). late=true면 바인딩을 재시도 */
    initModalStateTracking(late) {
      try {
        const bsIds = ['guideModal','knowhowModal','weeklyModal'];
        bsIds.forEach(id=>{
          const el = document.getElementById(id);
          if (!el) return;
          if (!el.__fab_bound) {
            el.addEventListener('shown.bs.modal', () => this.syncActiveState(this.mapModalToAction(id)));
            el.addEventListener('hidden.bs.modal', () => this.clearActiveAction());
            el.__fab_bound = true;
            this.log('bind bs modal events:', id);
          }
        });

        const customIds = ['claim-knowledge-modal','knowhow-modal','weekly-modal'];
        customIds.forEach(id=>{
          const el = document.getElementById(id);
          if (!el) return;
          if (!el.__fab_obs) {
            const obs = new MutationObserver((muts)=>{
              muts.forEach(m=>{
                if (m.type==='attributes' && (m.attributeName==='hidden' || m.attributeName==='class')) {
                  const shown = !el.hasAttribute('hidden') || el.classList.contains('show');
                  if (shown) this.syncActiveState(this.mapModalToAction(id));
                  else this.clearActiveAction();
                }
              });
            });
            obs.observe(el,{ attributes:true, attributeFilter:['hidden','class'] });
            el.__fab_obs = obs;
            this.log('observe custom modal:', id);
          }
        });

        const chatbot = document.getElementById('chatbot-container');
        if (chatbot && !chatbot.__fab_obs) {
          const ob = new MutationObserver((muts)=>{
            muts.forEach(m=>{
              if (m.type==='attributes' && m.attributeName==='style') {
                const shown = window.getComputedStyle(chatbot).display !== 'none';
                if (shown) this.syncActiveState('chatbot'); else this.clearActiveAction();
              }
            });
          });
          ob.observe(chatbot, { attributes:true, attributeFilter:['style'] });
          chatbot.__fab_obs = ob;
          this.log('observe chatbot container');
        }

        if (late) this.log('late modal watcher refresh');
      } catch (e) { this.handleError(e, 'initModalStateTracking'); }
    }

    mapModalToAction(id) {
      const m = {
        'guideModal':'guide',
        'knowhowModal':'knowhow',
        'knowhow-modal':'knowhow',
        'weeklyModal':'weekly',
        'weekly-modal':'weekly',
        'claim-knowledge-modal':'claim-knowledge',
        'chatbot-container':'chatbot'
      };
      return m[id] || '';
    }

    syncActiveState(action) {
      try {
        if (!action) return;
        if (this.activeAction === action) return;
        this.clearActiveAction();
        const el = document.querySelector(`[data-action="${action}"]`);
        if (el) this.setActiveAction(action, el);
        this.log('sync active from modal:', action);
      } catch (e) { this.handleError(e, 'syncActiveState'); }
    }

    executeAction(action) {
      try {
        this.log('execute:', action);
        switch (action) {
          case 'weekly': return this.executeWeekly();
          case 'knowhow': return this.executeKnowhow();
          case 'guide': return this.executeGuide();
          case 'claim-knowledge': return this.executeClaimKnowledge();
          case 'chatbot': return this.executeChatbot();
          default: this.warn('Unknown action:', action);
        }
      } catch (e) { this.handleError(e, 'executeAction'); }
    }

    // ===== 실행기 =====
    executeWeekly() {
      try {
        if (typeof window.openWeekly === 'function' && window.openWeekly()) return;
        // 혹시 실패하면 knowhow로 폴백(동일 UI인 프로젝트가 많음)
        if (typeof window.openKnowhow === 'function' && window.openKnowhow()) return;
        this.warn('weekly 실행 실패');
      } catch (e) { this.handleError(e, 'executeWeekly'); }
    }

    executeKnowhow() {
      try {
        if (typeof window.openKnowhow === 'function' && window.openKnowhow()) return;
        // weekly와 합쳐진 환경 폴백
        if (typeof window.openWeekly === 'function' && window.openWeekly()) return;
        this.warn('knowhow 실행 실패');
      } catch (e) { this.handleError(e, 'executeKnowhow'); }
    }

    executeGuide() {
      try {
        if (typeof window.openGuide === 'function' && window.openGuide()) return;
        const legacy = document.getElementById('guide-fab');
        if (legacy && typeof legacy.click === 'function') { legacy.click(); return; }
        this.warn('guide 실행 실패');
      } catch (e) { this.handleError(e, 'executeGuide'); }
    }

    executeClaimKnowledge() {
      try {
        if (typeof window.openClaimKnowledge === 'function' && window.openClaimKnowledge()) return;
        const m = document.getElementById('claim-knowledge-modal');
        if (m) { m.removeAttribute('hidden'); requestAnimationFrame(()=>m.classList.add('show')); return; }
        const legacy = document.getElementById('claim-knowledge-fab');
        if (legacy && typeof legacy.click === 'function') { legacy.click(); return; }
        this.warn('claim-knowledge 실행 실패');
      } catch (e) { this.handleError(e, 'executeClaimKnowledge'); }
    }

    executeChatbot() {
      try {
        const c = document.getElementById('chatbot-container');
        if (c) { c.style.display='block'; c.style.right='0'; c.style.transform='translateX(0)'; return; }
        const legacy = document.getElementById('chatbot-fab');
        if (legacy && typeof legacy.click === 'function') { legacy.click(); return; }
        this.warn('chatbot 실행 실패');
      } catch (e) { this.handleError(e, 'executeChatbot'); }
    }

    // ===== 공통 =====
    handleError(error, ctx) {
      console.error(`FAB Controller Error in ${ctx}:`, error);
      this.isExpanded = false;
      this.fabContainer?.classList?.remove('expanded');
      this.clearActiveAction();
      this.announce('일시적인 오류가 발생했습니다. 다시 시도해 주세요.');
    }

    announce(msg) {
      try {
        const d = document.createElement('div');
        d.setAttribute('aria-live','polite');
        d.setAttribute('aria-atomic','true');
        d.style.position='absolute'; d.style.left='-10000px';
        d.style.width='1px'; d.style.height='1px'; d.style.overflow='hidden';
        d.textContent = msg;
        document.body.appendChild(d);
        setTimeout(()=>document.body.removeChild(d), 1000);
      } catch (_) {}
    }
  }

  // DOM 준비 상태에 상관없이 보장 실행
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new FloatingFABController());
  } else {
    new FloatingFABController();
  }
})();
