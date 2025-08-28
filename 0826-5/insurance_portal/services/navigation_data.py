# -*- coding: utf-8 -*-
# insurance_portal/services/navigation_data.py
# Feature: 과실비율 챗봇 네비게이션 데이터
# Notes: 이 파일은 insurance_portal의 "과실비율 네비게이션" 기능에 사용됩니다.
# 기존 외부 API(views.fault_answer_view.navigation_data)가 기대하는 함수형 인터페이스
# (get_navigation_data, get_final_selection_summary)를 그대로 유지합니다.

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class NavigationDataManager:
    """
    교통사고 과실비율 네비게이션 데이터를 관리하는 클래스
    - navigation_tree는 아래와 같은 중첩 구조를 가정합니다.
      { "대분류": { "icon": ..., "description": ..., "children": {
            "중분류": { "icon": ..., "description": ..., "children": {
                "소분류": { "icon": ..., "description": ..., "options": [ ... ] }
            }}
        }}}
    """

    def __init__(self) -> None:
        self.navigation_tree: Dict[str, Any] = self._build_navigation_tree()

    def _build_navigation_tree(self) -> Dict[str, Any]:
        # 실제 프로젝트에서는 파일/DB에서 로드하도록 변경 가능.
        return {
            "교차로 사고": {
                "icon": "fas fa-traffic-light",
                "description": "교차로에서 발생한 사고",
                "children": {
                    "신호등 교차로": {
                        "icon": "fas fa-traffic-light",
                        "description": "신호등이 있는 교차로",
                        "children": {
                            "직진 vs 좌회전": {
                                "icon": "fas fa-arrows-alt-h",
                                "description": "직진 차량과 좌회전 차량 간 사고",
                                "options": [
                                    "직진차 신호준수 - 좌회전차 신호준수",
                                    "직진차 신호준수 - 좌회전차 신호위반",
                                    "직진차 신호위반 - 좌회전차 신호준수",
                                ],
                            }
                        },
                    }
                },
            },
            "추돌 사고": {
                "icon": "fas fa-car-crash",
                "description": "앞차를 뒤에서 추돌한 사고",
                "children": {
                    "일반 추돌": {
                        "icon": "fas fa-car-side",
                        "description": "일반적인 추돌 상황",
                        "children": {
                            "신호대기 중": {
                                "icon": "fas fa-pause-circle",
                                "description": "신호대기 중 추돌",
                                "options": [
                                    "정상 신호대기 중 - 후방 추돌",
                                    "급정거 - 후방 추돌",
                                    "신호위반 정지 - 후방 추돌",
                                ],
                            }
                        },
                    }
                },
            },
            "차로변경 사고": {
                "icon": "fas fa-car-side",
                "description": "차로를 변경하면서 발생한 사고",
                "children": {
                    "일반도로": {
                        "icon": "fas fa-road",
                        "description": "일반도로에서의 차로변경",
                        "children": {
                            "급진입": {
                                "icon": "fas fa-sign-in-alt",
                                "description": "급작스런 차로 진입",
                                "options": [
                                    "급작스런 차로변경",
                                    "안전거리 미확보",
                                    "방향지시등 미점등",
                                ],
                            }
                        },
                    }
                },
            },
        }

    def _descend(self, node: Dict[str, Any], step: str) -> Dict[str, Any]:
        """
        경로 한 단계(step)를 따라 내려간 노드를 반환.
        - 현재 노드의 dict에서 직접 키를 찾거나
        - children이 있으면 children에서 찾는다.
        """
        # 1) 현재 레벨 사전에서 직접 키 탐색
        if isinstance(node, dict) and step in node and isinstance(node[step], dict):
            return node[step]

        # 2) children 사전에 존재하면 그 안에서 탐색
        children = node.get("children")
        if isinstance(children, dict) and step in children and isinstance(children[step], dict):
            return children[step]

        raise KeyError(f"Invalid path: {step}")

    def get_navigation_data(self, path: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        현재 경로에 해당하는 네비게이션 데이터 반환
        """
        tree = self.navigation_tree or {}
        # 최상위
        if not path:
            return {
                "level": 0,
                "title": "교통사고 유형을 선택해주세요",
                "items": [
                    {
                        "key": key,
                        "title": key,
                        "icon": (node.get("icon") if isinstance(node, dict) else None) or "fas fa-list-ul",
                        "description": (node.get("description") if isinstance(node, dict) else None) or "",
                    }
                    for key, node in tree.items()
                ],
            }

        try:
            node: Dict[str, Any] = tree
            level = 0
            for step in path:
                node = self._descend(node, step)
                level += 1

            # children이 더 있으면 하위 선택지 제공
            if isinstance(node, dict) and isinstance(node.get("children"), dict):
                children = node["children"]
                return {
                    "level": level,
                    "path": path,
                    "title": f"{' > '.join(path)} 세부 유형을 선택해주세요",
                    "items": [
                        {
                            "key": k,
                            "title": k,
                            "icon": (v.get("icon") if isinstance(v, dict) else None) or "fas fa-list-ul",
                            "description": (v.get("description") if isinstance(v, dict) else None) or "",
                        }
                        for k, v in children.items()
                    ],
                }

            # 최종 선택 (options)
            if isinstance(node, dict) and isinstance(node.get("options"), list):
                return {
                    "level": level,
                    "path": path,
                    "title": f"{' > '.join(path)} 상세 상황을 선택해주세요",
                    "is_final": True,
                    "icon": node.get("icon"),
                    "description": node.get("description", ""),
                    "options": node["options"],
                }

            raise ValueError("Invalid node structure")

        except (KeyError, ValueError) as e:
            logger.error(f"Navigation error: {e}")
            # 에러 시 최상위 반환 (프론트는 에러 메시지 처리)
            return {
                "level": 0,
                "title": "교통사고 유형을 선택해주세요",
                "items": [
                    {
                        "key": key,
                        "title": key,
                        "icon": (nd.get("icon") if isinstance(nd, dict) else None) or "fas fa-list-ul",
                        "description": (nd.get("description") if isinstance(nd, dict) else None) or "",
                    }
                    for key, nd in (tree.items() if isinstance(tree, dict) else [])
                ],
            }

    def build_breadcrumb(self, path: List[str]) -> List[Dict[str, Any]]:
        return [{"label": p, "level": i} for i, p in enumerate(path or [])]

    def get_final_selection_summary(self, path: List[str], option: str) -> Dict[str, Any]:
        return {
            "category_path": path,
            "selected_option": option,
            "breadcrumb": self.build_breadcrumb(path),
            "query_context": f"{' > '.join(path)} > {option}",
            "search_keywords": list((path or [])) + ([option] if option else []),
        }


# ───── Singleton helpers ──────────────────────────────────────────────────────
_NAV_MANAGER: Optional[NavigationDataManager] = None

def _ensure_manager() -> NavigationDataManager:
    global _NAV_MANAGER
    if _NAV_MANAGER is None or not isinstance(_NAV_MANAGER, NavigationDataManager):
        _NAV_MANAGER = NavigationDataManager()
    return _NAV_MANAGER

def rebuild_navigation_manager() -> None:
    """
    외부에서 네비게이션 데이터를 갱신하고 싶을 때 호출.
    """
    global _NAV_MANAGER
    _NAV_MANAGER = NavigationDataManager()
    logger.info("[NAV] NavigationDataManager rebuilt")


# ───── Public functions (views 에서 사용) ─────────────────────────────────────
def get_navigation_data(path: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    네비게이션 데이터를 가져오는 편의 함수 (호출부 호환 유지)
    """
    manager = _ensure_manager()
    return manager.get_navigation_data(path)

def get_final_selection_summary(path: List[str], option: str) -> Dict[str, Any]:
    """
    최종 선택사항 요약을 가져오는 편의 함수 (호출부 호환 유지)
    """
    manager = _ensure_manager()
    return manager.get_final_selection_summary(path, option)
