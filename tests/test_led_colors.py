"""Tests for ledColors class."""
import pytest
from pytryfi.ledColors import ledColors


class TestLedColors:
    """Test ledColors class."""
    
    def test_init(self):
        """Test LED color initialization."""
        color = ledColors(1, "#FF00FF", "MAGENTA")
        assert color._ledColorCode == 1
        assert color._hexCode == "#FF00FF"
        assert color._name == "MAGENTA"
    
    def test_str_representation(self):
        """Test string representation."""
        color = ledColors(2, "#0000FF", "BLUE")
        result = str(color)
        
        assert "Color: BLUE" in result
        assert "Hex Code: #0000FF" in result
        assert "Color Code: 2" in result
    
    def test_all_properties(self):
        """Test all property getters."""
        color = ledColors(3, "#00FF00", "GREEN")
        
        assert color.name == "GREEN"
        assert color.ledColorCode == 3
        assert color.hexCode == "#00FF00"
    
    def test_various_color_codes(self):
        """Test with various LED color codes."""
        # Test all standard TryFi colors
        colors = [
            (1, "#FF00FF", "MAGENTA"),
            (2, "#0000FF", "BLUE"),
            (3, "#00FF00", "GREEN"),
            (4, "#FFFF00", "YELLOW"),
            (5, "#FFA500", "ORANGE"),
            (6, "#FF0000", "RED")
        ]
        
        for code, hex_val, name in colors:
            color = ledColors(code, hex_val, name)
            assert color.ledColorCode == code
            assert color.hexCode == hex_val
            assert color.name == name
    
    def test_edge_cases(self):
        """Test edge cases for LED colors."""
        # Test with 0 color code
        color = ledColors(0, "#000000", "BLACK")
        assert color.ledColorCode == 0
        assert color.hexCode == "#000000"
        assert color.name == "BLACK"
        
        # Test with negative color code
        color = ledColors(-1, "#FFFFFF", "WHITE")
        assert color.ledColorCode == -1
        assert color.hexCode == "#FFFFFF"
        assert color.name == "WHITE"
        
        # Test with large color code
        color = ledColors(999, "#123456", "CUSTOM")
        assert color.ledColorCode == 999
        assert color.hexCode == "#123456"
        assert color.name == "CUSTOM"
    
    def test_hex_code_variations(self):
        """Test various hex code formats."""
        # Standard 6-digit hex
        color = ledColors(1, "#FF00FF", "TEST1")
        assert color.hexCode == "#FF00FF"
        
        # Lowercase hex
        color = ledColors(2, "#ff00ff", "TEST2")
        assert color.hexCode == "#ff00ff"
        
        # Without # prefix (though not standard)
        color = ledColors(3, "FF00FF", "TEST3")
        assert color.hexCode == "FF00FF"
        
        # 3-digit hex
        color = ledColors(4, "#F0F", "TEST4")
        assert color.hexCode == "#F0F"
    
    def test_name_variations(self):
        """Test various name formats."""
        # Uppercase
        color = ledColors(1, "#000000", "UPPERCASE")
        assert color.name == "UPPERCASE"
        
        # Lowercase
        color = ledColors(2, "#000000", "lowercase")
        assert color.name == "lowercase"
        
        # Mixed case
        color = ledColors(3, "#000000", "MixedCase")
        assert color.name == "MixedCase"
        
        # With spaces
        color = ledColors(4, "#000000", "LIGHT BLUE")
        assert color.name == "LIGHT BLUE"
        
        # Empty string
        color = ledColors(5, "#000000", "")
        assert color.name == ""
        
        # Unicode
        color = ledColors(6, "#000000", "Röd")
        assert color.name == "Röd"
    
    def test_type_conversions(self):
        """Test type conversions for color code."""
        # String color code (will be stored as-is)
        color = ledColors("1", "#FF00FF", "MAGENTA")
        assert color.ledColorCode == "1"
        
        # Float color code
        color = ledColors(1.5, "#FF00FF", "MAGENTA")
        assert color.ledColorCode == 1.5
        
        # None values
        color = ledColors(None, None, None)
        assert color.ledColorCode is None
        assert color.hexCode is None
        assert color.name is None
    
    def test_immutability(self):
        """Test that properties are read-only."""
        color = ledColors(1, "#FF00FF", "MAGENTA")
        
        # Properties should not have setters
        with pytest.raises(AttributeError):
            color.name = "BLUE"
        
        with pytest.raises(AttributeError):
            color.ledColorCode = 2
        
        with pytest.raises(AttributeError):
            color.hexCode = "#0000FF"
    
    def test_equality(self):
        """Test equality between ledColors instances."""
        color1 = ledColors(1, "#FF00FF", "MAGENTA")
        color2 = ledColors(1, "#FF00FF", "MAGENTA")
        color3 = ledColors(2, "#0000FF", "BLUE")
        
        # Python default object equality (by reference)
        assert color1 != color2  # Different instances
        assert color1 != color3
        
        # But values should match
        assert color1.ledColorCode == color2.ledColorCode
        assert color1.hexCode == color2.hexCode
        assert color1.name == color2.name