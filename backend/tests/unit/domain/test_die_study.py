"""
Unit tests for Die Study Domain Entities.

Tests DieLink, DieStudyGroup, DieChain, and related enums.
"""

import pytest
from datetime import datetime, timezone

from src.domain.die_study import (
    DieSide,
    DieMatchConfidence,
    DieMatchSource,
    DieLink,
    DieStudyGroup,
    DieChain,
    DieComparisonResult,
)


class TestDieSide:
    """Tests for DieSide enum."""
    
    def test_values(self):
        """DieSide has obverse and reverse values."""
        assert DieSide.OBVERSE.value == "obverse"
        assert DieSide.REVERSE.value == "reverse"
    
    def test_from_string(self):
        """Can create from string value."""
        assert DieSide("obverse") == DieSide.OBVERSE
        assert DieSide("reverse") == DieSide.REVERSE


class TestDieMatchConfidence:
    """Tests for DieMatchConfidence enum."""
    
    def test_values(self):
        """DieMatchConfidence has expected values."""
        assert DieMatchConfidence.CERTAIN.value == "certain"
        assert DieMatchConfidence.PROBABLE.value == "probable"
        assert DieMatchConfidence.POSSIBLE.value == "possible"
        assert DieMatchConfidence.UNCERTAIN.value == "uncertain"


class TestDieMatchSource:
    """Tests for DieMatchSource enum."""
    
    def test_values(self):
        """DieMatchSource has expected values."""
        assert DieMatchSource.MANUAL.value == "manual"
        assert DieMatchSource.LLM.value == "llm"
        assert DieMatchSource.REFERENCE.value == "reference"
        assert DieMatchSource.IMPORT.value == "import"


class TestDieLink:
    """Tests for DieLink entity."""
    
    def test_create_link(self):
        """Can create a die link."""
        link = DieLink(
            coin_a_id=1,
            coin_b_id=2,
            die_side=DieSide.OBVERSE,
            confidence=DieMatchConfidence.CERTAIN,
            source=DieMatchSource.MANUAL,
        )
        
        assert link.coin_a_id == 1
        assert link.coin_b_id == 2
        assert link.die_side == DieSide.OBVERSE
        assert link.confidence == DieMatchConfidence.CERTAIN
    
    def test_cannot_link_coin_to_itself(self):
        """Cannot create a link between a coin and itself."""
        with pytest.raises(ValueError, match="itself"):
            DieLink(coin_a_id=1, coin_b_id=1, die_side=DieSide.OBVERSE)
    
    def test_requires_positive_ids(self):
        """Both coin IDs must be positive."""
        with pytest.raises(ValueError, match="positive"):
            DieLink(coin_a_id=0, coin_b_id=1, die_side=DieSide.OBVERSE)
        
        with pytest.raises(ValueError, match="positive"):
            DieLink(coin_a_id=1, coin_b_id=-1, die_side=DieSide.OBVERSE)
    
    def test_is_high_confidence(self):
        """is_high_confidence returns True for certain/probable."""
        certain = DieLink(
            coin_a_id=1, coin_b_id=2, die_side=DieSide.OBVERSE,
            confidence=DieMatchConfidence.CERTAIN
        )
        probable = DieLink(
            coin_a_id=1, coin_b_id=2, die_side=DieSide.OBVERSE,
            confidence=DieMatchConfidence.PROBABLE
        )
        possible = DieLink(
            coin_a_id=1, coin_b_id=2, die_side=DieSide.OBVERSE,
            confidence=DieMatchConfidence.POSSIBLE
        )
        
        assert certain.is_high_confidence is True
        assert probable.is_high_confidence is True
        assert possible.is_high_confidence is False
    
    def test_involves_coin(self):
        """involves_coin checks if coin is in link."""
        link = DieLink(coin_a_id=1, coin_b_id=2, die_side=DieSide.OBVERSE)
        
        assert link.involves_coin(1) is True
        assert link.involves_coin(2) is True
        assert link.involves_coin(3) is False
    
    def test_get_other_coin(self):
        """get_other_coin returns the other coin in the link."""
        link = DieLink(coin_a_id=1, coin_b_id=2, die_side=DieSide.OBVERSE)
        
        assert link.get_other_coin(1) == 2
        assert link.get_other_coin(2) == 1
    
    def test_get_other_coin_raises_for_non_member(self):
        """get_other_coin raises for coin not in link."""
        link = DieLink(coin_a_id=1, coin_b_id=2, die_side=DieSide.OBVERSE)
        
        with pytest.raises(ValueError, match="not in this die link"):
            link.get_other_coin(3)
    
    def test_with_reference_and_notes(self):
        """Can create link with reference and notes."""
        link = DieLink(
            coin_a_id=1,
            coin_b_id=2,
            die_side=DieSide.REVERSE,
            confidence=DieMatchConfidence.CERTAIN,
            source=DieMatchSource.REFERENCE,
            reference="RIC II, plate X.1",
            notes="Clear die match visible in hair curls",
        )
        
        assert link.reference == "RIC II, plate X.1"
        assert "hair curls" in link.notes


class TestDieStudyGroup:
    """Tests for DieStudyGroup entity."""
    
    def test_create_group(self):
        """Can create a die study group."""
        group = DieStudyGroup(
            name="Trajan Obverse Die A",
            die_side=DieSide.OBVERSE,
            issuer_id=42,
            notes="Main portrait die used early in reign",
        )
        
        assert group.name == "Trajan Obverse Die A"
        assert group.die_side == DieSide.OBVERSE
        assert group.issuer_id == 42
        assert group.members == []
    
    def test_add_member(self):
        """Can add members to group."""
        group = DieStudyGroup(name="Test", die_side=DieSide.OBVERSE)
        
        group.add_member(1)
        group.add_member(2, position=1)
        group.add_member(3, position=2)
        
        assert group.member_count == 3
        assert 1 in group.members
        assert 2 in group.members
        assert group.member_positions[2] == 1
        assert group.member_positions[3] == 2
    
    def test_add_member_idempotent(self):
        """Adding same member twice doesn't duplicate."""
        group = DieStudyGroup(name="Test", die_side=DieSide.OBVERSE)
        
        group.add_member(1)
        group.add_member(1)  # Second add
        
        assert group.member_count == 1
    
    def test_remove_member(self):
        """Can remove members from group."""
        group = DieStudyGroup(name="Test", die_side=DieSide.OBVERSE)
        group.add_member(1, position=1)
        group.add_member(2, position=2)
        
        removed = group.remove_member(1)
        
        assert removed is True
        assert group.member_count == 1
        assert 1 not in group.members
        assert 1 not in group.member_positions
    
    def test_remove_non_member_returns_false(self):
        """Removing non-member returns False."""
        group = DieStudyGroup(name="Test", die_side=DieSide.OBVERSE)
        
        removed = group.remove_member(99)
        
        assert removed is False


class TestDieChain:
    """Tests for DieChain view object."""
    
    def test_create_chain(self):
        """Can create a die chain."""
        link1 = DieLink(coin_a_id=1, coin_b_id=2, die_side=DieSide.OBVERSE)
        link2 = DieLink(coin_a_id=2, coin_b_id=3, die_side=DieSide.OBVERSE)
        
        chain = DieChain(
            coins=[1, 2, 3],
            links=[link1, link2],
            die_side=DieSide.OBVERSE,
        )
        
        assert chain.length == 3
        assert chain.contains(2)
        assert not chain.contains(99)


class TestDieComparisonResult:
    """Tests for DieComparisonResult."""
    
    def test_create_match_result(self):
        """Can create a comparison result for a match."""
        result = DieComparisonResult(
            coin_a_id=1,
            coin_b_id=2,
            die_side=DieSide.OBVERSE,
            is_match=True,
            confidence=0.95,
            reasoning=["Portrait style identical", "Same die crack at 2 o'clock"],
            diagnostic_points=["Hair curls", "Legend spacing"],
        )
        
        assert result.is_match is True
        assert result.confidence == 0.95
        assert len(result.reasoning) == 2
        assert "Hair curls" in result.diagnostic_points
    
    def test_create_non_match_result(self):
        """Can create a comparison result for non-match."""
        result = DieComparisonResult(
            coin_a_id=1,
            coin_b_id=2,
            die_side=DieSide.REVERSE,
            is_match=False,
            confidence=0.1,
            reasoning=["Different legend arrangement", "Different figure positioning"],
        )
        
        assert result.is_match is False
        assert result.confidence == 0.1
