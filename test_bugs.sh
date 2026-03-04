#!/bin/bash
# Bug Verification Tests
echo "=== BUG VERIFICATION TESTS ==="
echo ""

# BUG-1: Search API Test
echo "BUG-1: Testing Search API..."
SEARCH_RESULT=$(curl -s "http://192.144.12.24/api/v1/search?q=%D1%82%D0%B5%D1%81%D1%82&page=1&per_page=5")
SEARCH_TOTAL=$(echo $SEARCH_RESULT | python3 -c "import sys,json; print(json.load(sys.stdin).get('total',0))" 2>/dev/null)
if [ "$SEARCH_TOTAL" -gt 0 ]; then
    echo "✅ BUG-1: Search API returns $SEARCH_TOTAL results"
else
    echo "❌ BUG-1: Search API returns empty"
fi
echo ""

# BUG-2: Authors API (needed for Add Book)
echo "BUG-2: Testing Authors API for Add Book..."
AUTHORS_RESULT=$(curl -s "http://192.144.12.24/api/v1/authors")
AUTHORS_COUNT=$(echo $AUTHORS_RESULT | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$AUTHORS_COUNT" -gt 0 ]; then
    echo "✅ BUG-2: Authors API returns $AUTHORS_COUNT authors (Add Book can populate dropdown)"
else
    echo "❌ BUG-2: Authors API returns empty"
fi
echo ""

# BUG-3: Test Author Creation API
echo "BUG-3: Testing Author Creation API..."
# Try to get token first
echo "Note: POST /api/v1/authors requires auth - endpoint exists"
curl -s -X POST "http://192.144.12.24/api/v1/authors" -H "Content-Type: application/json" -d '{"name":"Test"}' | grep -q "Not authenticated" && echo "✅ BUG-3: POST /api/v1/authors endpoint exists (requires auth)" || echo "? BUG-3: Check endpoint"
echo ""

# BUG-3: Test Library Creation API
echo "BUG-3: Testing Library Creation API..."
curl -s -X POST "http://192.144.12.24/api/v1/libraries" -H "Content-Type: application/json" -d '{"name":"Test","address":"Test"}' | grep -q "Not authenticated" && echo "✅ BUG-3: POST /api/v1/libraries endpoint exists (requires auth)" || echo "? BUG-3: Check endpoint"
echo ""

# BUG-4: Test Copy Creation API
echo "BUG-4: Testing Copy Creation API..."
curl -s -X POST "http://192.144.12.24/api/v1/books/24/copies" -H "Content-Type: application/json" -d '{"library_id":1}' | grep -q "Not authenticated" && echo "✅ BUG-4: POST /api/v1/books/{id}/copies endpoint exists (requires auth)" || echo "? BUG-4: Check endpoint"
echo ""

echo "=== END OF TESTS ==="
