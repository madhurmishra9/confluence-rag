# Code Citations

## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: MIT
https://github.com/iethan/MachineLearning/blob/b46a6168b8b0329c854398c8895b64415cc066ed/MachineLearning/pre_processing/clean_text.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: MIT
https://github.com/iethan/MachineLearning/blob/b46a6168b8b0329c854398c8895b64415cc066ed/MachineLearning/pre_processing/clean_text.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: MIT
https://github.com/iethan/MachineLearning/blob/b46a6168b8b0329c854398c8895b64415cc066ed/MachineLearning/pre_processing/clean_text.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: MIT
https://github.com/iethan/MachineLearning/blob/b46a6168b8b0329c854398c8895b64415cc066ed/MachineLearning/pre_processing/clean_text.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: MIT
https://github.com/iethan/MachineLearning/blob/b46a6168b8b0329c854398c8895b64415cc066ed/MachineLearning/pre_processing/clean_text.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: MIT
https://github.com/iethan/MachineLearning/blob/b46a6168b8b0329c854398c8895b64415cc066ed/MachineLearning/pre_processing/clean_text.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: MIT
https://github.com/iethan/MachineLearning/blob/b46a6168b8b0329c854398c8895b64415cc066ed/MachineLearning/pre_processing/clean_text.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _
```


## License: MIT
https://github.com/iethan/MachineLearning/blob/b46a6168b8b0329c854398c8895b64415cc066ed/MachineLearning/pre_processing/clean_text.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: unknown
https://github.com/rashaini/asameena/blob/66d54c18a72b5b71204412f3b339fc0ec51ea678/macmillan_spider_v1/macmillan_spider_v1/spiders/mac_spider.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: MIT
https://github.com/iethan/MachineLearning/blob/b46a6168b8b0329c854398c8895b64415cc066ed/MachineLearning/pre_processing/clean_text.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: GPL-3.0
https://github.com/BlackHoleSecurity/contexploit/blob/b824e2929b11209d9ee62820c04d2fc79c41bc99/contexploit.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: unknown
https://github.com/zia-muhammad/Newsrecommender/blob/276300714371da227d7af9c1ff12ffcc41a1924e/src/main/python/news_articles_processor.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```


## License: unknown
https://github.com/itl-projects/ScrapeWebsites_v0.1/blob/24f2294e4ef7d033b0a0c345c5504e97111c1d55/utils.py

```
The fetch is taking long because of several bottlenecks. Here are the issues and fixes:

**Problems:**
1. **Sequential requests** - Fetches pages one batch at a time (50 pages per request)
2. **No connection pooling optimization** - Default session settings aren't tuned
3. **HTML parsing overhead** - BeautifulSoup parses every page's HTML
4. **Logging verbosity** - Logging every single page slows down I/O

**Optimized version:**

````python
// filepath: c:\Users\Madhur\Desktop\confluence-rag\src\fetch_confluence.py
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfluenceFetcher:
    """Fetches pages from Confluence REST API with pagination"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        """
        Initialize Confluence fetcher with optimized connection pooling
        """
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json'})
        
        # Connection pooling optimization
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def _strip_html(self, html_content: str) -> str:
        """Strip HTML tags from content using BeautifulSoup"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def _process_page(self, page:
```

