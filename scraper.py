import requests
from bs4 import BeautifulSoup
import config

import requests
from bs4 import BeautifulSoup
import config
import os
from urllib.parse import urljoin

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64

class ECAPScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _save_debug(self, content, filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

    def _encrypt_password(self, password):
        # Key and IV from the JS source: '8701661282118308'
        key = b'8701661282118308'
        iv = b'8701661282118308'
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(password.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        # Checking JS: CryptoJS default output is Base64
        return base64.b64encode(encrypted).decode('utf-8')

    def login(self, username, password):
        try:
            # 1. Get Login Page
            response = self.session.get(config.LOGIN_URL, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the form and its action
            form = soup.find('form', {'id': 'form1'})
            if not form:
                return False, "Could not find login form."
                
            action = form.get('action')
            post_url = urljoin(config.LOGIN_URL, action) if action else config.LOGIN_URL
            
            # Collect all hidden inputs
            data = {inp.get('name'): inp.get('value') for inp in soup.find_all('input', {'type': 'hidden'}) if inp.get('name')}
            
            # Encrypt Password
            encrypted_password = self._encrypt_password(password)
            
            # Add specific credentials
            # IMPORTANT: The JS copies encrypted val back to txtPwd2
            data.update({
                'txtId2': username,
                'txtPwd2': encrypted_password, 
                'hdnpwd2': encrypted_password, # Send this too just in case
                'imgBtn2.x': '15',
                'imgBtn2.y': '15'
            })
            
            # 2. POST Login
            post_response = self.session.post(post_url, data=data, headers=self.headers)
            
            # Check for failure
            if "txtId2" in post_response.text:
                soup_post = BeautifulSoup(post_response.text, 'html.parser')
                err = soup_post.find('span', {'id': 'lblError1'}) if soup_post.find('span', {'id': 'lblError1'}) else soup_post.find('span', {'id': 'lblError2'})
                err_msg = err.get_text(strip=True) if err else "Unknown Login Error"
                self._save_debug(post_response.text, "debug_login_failed.html")
                return False, f"Login Failed: {err_msg}"

            return True, "Login successful"

        except Exception as e:
            return False, f"Exception during login: {str(e)}"

    def get_attendance(self):
        try:
            # 1. Get the Attendance Page to find the Ajax URL and Roll No
            attendance_url = config.BASE_URL + "Academics/StudentAttendance.aspx"
            response = self.session.get(attendance_url, headers=self.headers)
            
            if "Login.aspx" in response.url or "txtId2" in response.text:
                return None # Session lost
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the Ajax URL from script tag
            ajax_script = soup.find('script', src=lambda s: s and 'ajax/StudentAttendance' in s)
            if not ajax_script:
                print("Could not find Ajax script.")
                self._save_debug(response.text, "debug_attendance_no_ajax.html")
                return None
                
            ajax_path = ajax_script['src']
            ajax_url = urljoin(config.BASE_URL, ajax_path)
            
            # Find the Roll Number from hidden field
            hdn_roll = soup.find('input', {'id': 'ctl00_CapPlaceHolder_hdnType'})
            if hdn_roll and hdn_roll.get('value'):
                roll_no = hdn_roll.get('value')
            else:
                roll_no = ""
            
            # AjaxPro format based on the JavaScript:
            # ShowAttendance:function(rollNo,fromDate,toDate,excludeothersubjects,callback,context)
            # Body format: 'rollNo=' + enc(rollNo)+ '\r\nfromDate=' + enc(fromDate)+ '\r\ntoDate=' + enc(toDate)+ '\r\nexcludeothersubjects=' + enc(excludeothersubjects)
            
            # Construct the body in AjaxPro format
            body = f"rollNo={roll_no}\r\nfromDate=\r\ntoDate=\r\nexcludeothersubjects=false"
            
            # Headers for AjaxPro
            ajax_headers = self.headers.copy()
            ajax_headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=utf-8'
            ajax_headers['X-AjaxPro-Method'] = 'ShowAttendance'
            
            # Make the request with query parameter
            full_ajax_url = ajax_url + '?_method=ShowAttendance&_session=r'
            
            response_ajax = self.session.post(full_ajax_url, data=body, headers=ajax_headers)
            
            # AjaxPro returns the HTML as a JavaScript string literal
            # Format: '<center><div>...</div></center>'
            text = response_ajax.text.strip()
            
            # Remove surrounding quotes if present
            if text.startswith("'") and text.endswith("'"):
                html_table = text[1:-1]
                # Unescape JavaScript string escapes
                html_table = html_table.replace("\\'", "'").replace("\\\\", "\\")
                return html_table
            
            # Try JSON format (/*JSON*/{...}/*JSON*/)
            import re
            json_match = re.search(r'/\*JSON\*/(.+?)/\*JSON\*/', text)
            if json_match:
                import json
                result_json = json.loads(json_match.group(1))
                if result_json.get('error'):
                    print(f"Ajax Error: {result_json['error']}")
                    return None
                
                html_table = result_json.get('value')
                return html_table
            
            # Try plain JSON
            try:
                import json
                result_json = json.loads(text)
                if result_json.get('error'):
                    print(f"Ajax Error: {result_json['error']}")
                    return None
                
                html_table = result_json.get('value')
                return html_table
            except:
                # If all parsing fails, return the raw text
                self._save_debug(text, "debug_ajax_parse_failed.txt")
                print("Failed to parse Ajax response")
                return None

        except Exception as e:
            print(f"Scraping Error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_todays_attendance(self):
        """Fetch today's attendance (P/A status) from Academic Register page"""
        try:
            from datetime import datetime
            
            # The correct URL from FillScreens response
            register_url = config.BASE_URL + "Academics/studentacadamicregister.aspx?scrid=2"
            response = self.session.get(register_url, headers=self.headers)
            
            if "Login.aspx" in response.url or "txtId2" in response.text:
                return None  # Session lost
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the div that contains the register data
            div = soup.find('div', id='ctl00_CapPlaceHolder_divRegister')
            if not div:
                print("Could not find divRegister")
                return {}
            
            # Find all tables inside this div
            tables = div.find_all('table')
            print(f"Found {len(tables)} tables inside divRegister")
            
            # The attendance table is the one with date headers (usually the last/largest table)
            attendance_table = None
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 10:  # Attendance table has many rows (subjects)
                    # Check if first row has date-like headers
                    first_row = rows[0]
                    cells = first_row.find_all(['td', 'th'])
                    if len(cells) > 10:  # Many date columns
                        cell_text = ' '.join([c.get_text(strip=True) for c in cells[:5]])
                        if '/' in cell_text or 'Subject' in cell_text:
                            attendance_table = table
                            break
            
            if not attendance_table:
                print("Could not find attendance table in divRegister")
                return {}
            
            rows = attendance_table.find_all('tr')
            if len(rows) < 2:
                print(f"Table has only {len(rows)} rows")
                return {}
            
            # First row contains dates (headers)
            header_row = rows[0]
            date_cells = header_row.find_all(['td', 'th'])
            
            # Find today's date column
            today = datetime.now()
            today_str = f"{today.day:02d}/{today.month:02d}"  # Format: DD/MM
            
            print(f"Looking for today's date: {today_str}")
            print(f"Found {len(date_cells)} header cells")
            
            today_col_idx = -1
            for i, cell in enumerate(date_cells):
                cell_text = cell.get_text(strip=True)
                # Match formats like "15/12", "16/12", or just "15", "16"
                if today_str in cell_text or cell_text == str(today.day):
                    today_col_idx = i
                    print(f"Found today's column at index {i}: '{cell_text}'")
                    break
            
            if today_col_idx == -1:
                print(f"Could not find today's date column")
                # Show first 10 date columns for debugging
                print("First 10 date columns:")
                for i, cell in enumerate(date_cells[:10]):
                    print(f"  {i}: '{cell.get_text(strip=True)}'")
                return {}
            
            # Parse each subject row
            todays_attendance = {}
            for row in rows[1:]:
                cells = row.find_all('td')
                if len(cells) <= today_col_idx or len(cells) < 2:
                    continue
                
                # Column 0: Sl.No
                # Column 1: Subject name
                # Column 2+: Date columns
                subject_name = cells[1].get_text(strip=True)
                
                # Skip if no subject name
                if not subject_name or subject_name == '-':
                    continue
                
                # Get today's attendance status
                status_cell = cells[today_col_idx]
                # Get raw text and clean it - remove &nbsp; and extra spaces
                status = status_cell.get_text(strip=True).replace('&nbsp;', '').replace(' ', '')
                
                # Only include if there's actual attendance data (contains P or A)
                if status and status != '-' and ('P' in status or 'A' in status):
                    # Store the raw P/A sequence (e.g., "P", "PP", "PPP", "PAP", etc.)
                    todays_attendance[subject_name] = status
            
            print(f"Found {len(todays_attendance)} subjects with today's attendance")
            return todays_attendance
            
        except Exception as e:
            print(f"Error fetching today's attendance: {e}")
            import traceback
            traceback.print_exc()
            return {}

