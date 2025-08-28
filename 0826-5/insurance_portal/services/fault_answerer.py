# -*- coding: utf-8 -*-
# insurance_portal/services/fault_answerer.py
# Feature: 과실비율 챗봇 | Purpose: 네비게이션 선택/질의에 대한 과실비율 응답 생성
# Notes: 이 파일은 insurance_portal.views.fault_answer_view에서 import되어 사용됩니다.

from __future__ import annotations
from typing import Dict, Any, List, Optional

__all__ = ["answer_fault"]


def _result(
    base_fault: Optional[str] = None,
    base_fault_description: Optional[str] = None,
    adjustments: Optional[List[str]] = None,
    references: Optional[List[str]] = None,
    summary: Optional[str] = None,
    needs_more_input: bool = False,
    questions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "base_fault": base_fault,
        "base_fault_description": base_fault_description,
        "adjustments": adjustments or [],
        "references": references or [],
        "summary": summary,
        "needs_more_input": needs_more_input,
        "questions": questions or [],
    }


def _match_by_path(navigation_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    네비게이션 경로/옵션을 기반으로 간단한 룰 매칭.
    실제 서비스에서는 RAG/룰/LLM 등을 결합하세요.
    """
    path = (navigation_context or {}).get("path") or []
    option = (navigation_context or {}).get("selected_option")
    joined = " > ".join(path + ([option] if option else []))

    # 예시 규칙 1: 차로변경 사고 > 일반도로 > 급진입
    if path[:2] == ["차로변경 사고", "일반도로"] and (option == "급작스런 차로변경" or "급진입" in (option or "")):
        return _result(
            base_fault="차로변경차 70 : 직진차 30",
            base_fault_description="일반도로에서 급작스러운 차로 진입으로 인한 사고의 기본 과실 예시치입니다.",
            adjustments=[
                "방향지시등 미점등: 차로변경차 +10",
                "충분한 안전거리 미확보: 후방차 +10",
                "야간/우천 등 시야불량: 가해차 +10",
            ],
            references=[
                "차로변경 관련 도로교통법 시행규칙",
                "국내 손해보험 과실비율 인정기준(예시)",
            ],
            summary=f"[요약] {joined} 상황으로 판단되어 기본 70:30에서 가감요소에 따라 변동될 수 있습니다.",
        )

    # 예시 규칙 2: 교차로 사고 > 신호등 교차로 > 직진 vs 좌회전
    if path[:2] == ["교차로 사고", "신호등 교차로"] and (path[-1] == "직진 vs 좌회전" or "좌회전" in (joined)):
        return _result(
            base_fault="좌회전차 60 : 직진차 40",
            base_fault_description="신호 준수 전제에서 좌회전차의 주의의무가 상대적으로 큽니다.",
            adjustments=[
                "직진차 과속: 직진차 +10",
                "좌회전차 신호 미준수: 좌회전차 +20",
                "비보호 좌회전 구간: 좌회전차 +10",
            ],
            references=[
                "비보호 좌회전 관련 해설",
                "교차로 통행방법(도로교통법) 판례 요약",
            ],
            summary=f"[요약] {joined} 상황으로 판단되어 기본 60:40에서 가감요소에 따라 변동될 수 있습니다.",
        )

    # 예시 규칙 3: 추돌 사고 > 일반 추돌 > 신호대기 중
    if path[:2] == ["추돌 사고", "일반 추돌"] and (path[-1] == "신호대기 중" or "신호대기" in (joined)):
        return _result(
            base_fault="후방차 100 : 선행차 0",
            base_fault_description="정상 신호대기 중 후방 추돌은 후방차 전적인 과실로 보는 것이 일반적입니다.",
            adjustments=[
                "선행차의 급정거: 후방차 -20, 선행차 +20",
                "선행차의 후진: 선행차 +30",
            ],
            references=[
                "후방추돌 과실비율 내부기준(예시)",
            ],
            summary=f"[요약] {joined} 상황으로 판단되어 기본 100:0에서 일부 특수사정에 따라 조정 가능합니다.",
        )

    return None


def answer_fault(
    query: Optional[str],
    navigation_context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    퍼블릭 진입점. 네비게이션 컨텍스트 우선으로 결과를 생성합니다.
    반환 형식은 프런트엔드가 기대하는 스키마를 따릅니다.
    """
    # 1) 네비게이션 경로 기반 룰 매칭
    if navigation_context:
        matched = _match_by_path(navigation_context)
        if matched:
            return matched

    # 2) 텍스트 질의 기반(간단 키워드 예시)
    q = (query or "").strip()
    if q:
        if "차로변경" in q and ("급진입" in q or "급작" in q):
            return _result(
                base_fault="차로변경차 70 : 직진차 30",
                base_fault_description="일반도로 급진입 차로변경 사고의 예시 과실비율입니다.",
                adjustments=[
                    "방향지시등 미점등: 차로변경차 +10",
                ],
                summary="[요약] 차로변경 급진입 상황으로 판단됩니다.",
            )
        if "후방" in q or "추돌" in q:
            return _result(
                base_fault="후방차 100 : 선행차 0",
                base_fault_description="일반적인 후방 추돌의 기본 과실 예시입니다.",
                summary="[요약] 후방 추돌로 판단됩니다.",
            )

    # 3) 추가 정보 필요
    return _result(
        summary="정확한 판단을 위해 사고 유형/장소/행동(차로변경, 급진입 등) 중 최소 1가지를 더 알려주세요.",
        needs_more_input=True,
        questions=[
            "사고 장소가 교차로/일반도로/고속도로 중 어디인가요?",
            "차로 변경 중이었나요?",
            "상대 차량의 진행 상태(정지/저속/정상주행)는 어땠나요?",
        ],
    )
