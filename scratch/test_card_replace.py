import re

html_sample = '''
<div class="evidence-card" style="border-left: 3px solid #a855f7;">
    <div class="evidence-header">
        <span class="evidence-title flex items-center gap-1.5">Office365: Registered Account</span>
        <span class="evidence-tag" style="background: rgba(168, 85, 247, 0.15); color: #c084fc;">EMAIL REGISTRATION VERIFIED</span>
    </div>
    <div class="evidence-body">Intelligence Signal: Registered account verified on Office365</div>
</div>
'''

bStyle = 'background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);'
bLabel = '[PROFILES & ACCOUNTS]'
categoryPillHtml = f'<span class="pivot-category-pill" style="{bStyle}">{bLabel}</span>'

# Test replacement
result = re.sub(
    r'<span class="evidence-tag"([^>]*)>(.*?)</span>',
    f'<div class="evidence-tags-group">{categoryPillHtml}<span class="evidence-tag"\\1>\\2</span></div>',
    html_sample,
    flags=re.DOTALL
)

print('Generated HTML:')
print(result)
assert '<div class="evidence-tags-group">' in result
assert '[PROFILES & ACCOUNTS]' in result
assert 'EMAIL REGISTRATION VERIFIED' in result
print('SUCCESS: Both badges cleanly nested side-by-side inside evidence-tags-group without negative margins!')
