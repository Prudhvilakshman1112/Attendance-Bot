from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

def parse_attendance(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the table with class='cellBorder' - this is the attendance data table
    table = soup.find('table', class_='cellBorder')
    
    if not table:
        print("Could not find table with class='cellBorder'")
        return None
    
    rows = table.find_all('tr')
    print(f"Found table with {len(rows)} rows")
    
    subjects = []
    total_classes = 0
    total_present = 0
    
    # Process each row
    for i, row in enumerate(rows):
        cells = row.find_all('td')
        
        if len(cells) != 5:
            continue  # Skip rows that don't have exactly 5 cells
        
        # Get cell contents
        sl_no = cells[0].get_text(strip=True)
        subject = cells[1].get_text(strip=True)
        held = cells[2].get_text(strip=True)
        attend = cells[3].get_text(strip=True)
        percent = cells[4].get_text(strip=True)
        
        # Skip header row and TOTAL row
        if 'subject' in subject.lower() or 'total' in subject.lower():
            continue
        
        # Try to parse as numbers
        try:
            conducted = int(held)
            attended = int(attend)
        except ValueError:
            continue
        
        pc = (attended / conducted * 100) if conducted > 0 else 0.0
        
        subjects.append({
            'name': subject,
            'conducted': conducted,
            'attended': attended,
            'percent': pc
        })
        
        total_classes += conducted
        total_present += attended
    
    if not subjects:
        print("No subjects found")
        return None
    
    overall_percent = (total_present / total_classes * 100) if total_classes > 0 else 0
    
    data = {
        'subjects': subjects,
        'total_classes': total_classes,
        'total_present': total_present,
        'overall_percent': overall_percent,
        'last_updated': datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%d/%m/%Y, %I:%M:%S %p")
    }
    
    return data

def calculate_skip_hours(total_present, total_classes, target_percent=75):
    if total_classes == 0: return 0, "No classes yet"
    
    current_percent = (total_present / total_classes) * 100
    
    if current_percent >= target_percent:
        max_total = total_present / (target_percent / 100.0)
        skippable = int(max_total - total_classes)
        return skippable, f"You can skip {skippable} hours and still maintain above {target_percent}%."
    else:
        needed = ( (target_percent/100.0 * total_classes) - total_present ) / (1 - (target_percent/100.0))
        import math
        needed = math.ceil(needed)
        return needed, f"You need to attend {needed} more hours to reach {target_percent}%."

def format_message(data, username, todays_attendance=None):
    if not data:
        return "❌ Failed to fetch data."
        
    skip_hours, advice = calculate_skip_hours(data['total_present'], data['total_classes'], 75)
    
    # Header with student info
    msg = f"👤 **Roll Number:** `{username}`\n"
    msg += f"📊 **Total Attendance:** {data['total_present']}/{data['total_classes']} ({data['overall_percent']:.2f}%)\n\n"
    
    # Attendance status emoji based on percentage
    percent = data['overall_percent']
    if percent >= 90:
        status_emoji = "🟢"
    elif percent >= 75:
        status_emoji = "🟡"
    else:
        status_emoji = "🔴"
    
    msg += f"{status_emoji} {advice}\n\n"
    
    # Add Today's Attendance if available
    if todays_attendance:
        msg += "📅 **Today's Attendance:**\n"
        for subject, status in todays_attendance.items():
            # Add emoji based on status
            if 'A' in status:
                status_emoji = "❌"
            else:
                status_emoji = "✅"
            msg += f"  {status_emoji} {subject}: `{status}`\n"
        msg += "\n"
    
    msg += "📚 **Subject-wise Attendance:**\n"
    for sub in data['subjects']:
        # Emoji based on subject percentage
        if sub['percent'] >= 90:
            emoji = "🟢"
        elif sub['percent'] >= 75:
            emoji = "🟡"
        else:
            emoji = "🔴"
        
        msg += f"  {emoji} {sub['name']}: {sub['attended']}/{sub['conducted']} ({sub['percent']:.2f}%)\n"
        
    msg += f"\n🕐 **Last Updated:** {data['last_updated']}"
    return msg
