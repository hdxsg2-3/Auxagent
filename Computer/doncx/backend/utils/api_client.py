import requests
import time
import json
from config import Config
from utils.logger import log_error, log_api_call
from utils.volc_sign import VolcSigner

class APIClient:
    def __init__(self):
        self.api_key = Config.API_KEY
        self.api_endpoint = Config.API_ENDPOINT
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        # 火山机器翻译 / 内容安全 使用 AK/SK 签名，不依赖方舟 Token
        self.trans_ak = Config.VOLC_TRANS_AK
        self.trans_sk = Config.VOLC_TRANS_SK
        self.content_ak = Config.VOLC_CONTENT_AK
        self.content_sk = Config.VOLC_CONTENT_SK
    
    def call_llm(self, messages, model=None, temperature=None, max_tokens=None):
        if not self.api_key:
            log_error('APIClient', 'API key is not configured')
            return None, 'API密钥未配置，请在系统设置中配置'

        if not self.api_endpoint:
            log_error('APIClient', 'API endpoint is not configured')
            return None, 'API接口地址未配置，请在系统设置中配置'

        start_time = time.time()
        try:
            url = f'{self.api_endpoint}/chat/completions'
            payload = {
                'model': model or Config.MODEL_NAME,
                'messages': messages,
                'temperature': temperature or Config.TEMPERATURE,
                'max_tokens': max_tokens or Config.MAX_TOKENS
            }
            response = requests.post(url, headers=self.headers, json=payload, timeout=Config.TIMEOUT)
            response.raise_for_status()
            result = response.json()

            latency = int((time.time() - start_time) * 1000)
            log_api_call('llm', url, self._truncate_payload(payload), result, 'success', latency)

            if result.get('choices'):
                return result['choices'][0]['message']['content'], None
            return None, 'API返回格式异常'
        except requests.exceptions.Timeout:
            latency = int((time.time() - start_time) * 1000)
            log_api_call('llm', url, self._truncate_payload(payload if 'payload' in locals() else {}), {}, 'failed', latency)
            log_error('APIClient', 'API connection timeout')
            return None, 'API连接超时，请检查网络或稍后重试'
        except requests.exceptions.ConnectionError:
            latency = int((time.time() - start_time) * 1000)
            log_api_call('llm', url, self._truncate_payload(payload if 'payload' in locals() else {}), {}, 'failed', latency)
            log_error('APIClient', 'API connection error')
            return None, 'API连接失败，请检查网络或API地址是否正确'
        except requests.exceptions.HTTPError as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call('llm', url, self._truncate_payload(payload if 'payload' in locals() else {}), {}, 'failed', latency)
            log_error('APIClient', f'HTTP error: {str(e)}')
            return None, f'API请求失败: {str(e)}'
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call('llm', url, self._truncate_payload(payload if 'payload' in locals() else {}), {}, 'failed', latency)
            log_error('APIClient', e)
            return None, 'API调用异常，请检查配置或稍后重试'

    @staticmethod
    def _truncate_payload(payload):
        """截断日志中的图片 base64 数据，避免日志过大。"""
        if not isinstance(payload, dict):
            return payload
        sanitized = {}
        for k, v in payload.items():
            if k == 'messages' and isinstance(v, list):
                sanitized[k] = []
                for msg in v:
                    if not isinstance(msg, dict):
                        sanitized[k].append(msg)
                        continue
                    new_msg = dict(msg)
                    if isinstance(new_msg.get('content'), list):
                        new_content = []
                        for part in new_msg['content']:
                            if isinstance(part, dict) and part.get('type') == 'image_url':
                                url = part.get('image_url', {}).get('url', '') or ''
                                new_content.append({
                                    'type': 'image_url',
                                    'image_url': {'url': (url[:80] + '...[truncated]') if len(url) > 80 else url}
                                })
                            else:
                                new_content.append(part)
                        new_msg['content'] = new_content
                    sanitized[k].append(new_msg)
            elif isinstance(v, str) and len(v) > 1000:
                sanitized[k] = v[:1000] + '...[truncated]'
            else:
                sanitized[k] = v
        return sanitized

    # ============ 火山机器翻译（AK/SK 签名） ============
    def call_translate(self, texts, target_language, source_language=''):
        """调用火山机器翻译，texts 为待译文本列表，返回翻译后列表或 (None, error)。"""
        if not self.trans_ak:
            return None, '机器翻译 AK 未配置'
        try:
            signer = VolcSigner(self.trans_ak, self.trans_sk)
            host = 'translate.volcengineapi.com'
            region = 'cn-north-1'
            service = 'translate'
            path = '/'
            query = {'Action': 'TranslateText', 'Version': '2020-06-01'}
            body = json.dumps({
                'SourceLanguage': source_language,
                'TargetLanguage': target_language,
                'TextList': texts,
            }, ensure_ascii=False)

            headers, query_string = signer.sign('POST', host, region, service, path, query, body)
            url = f'https://{host}{path}' + (f'?{query_string}' if query_string else '')

            resp = requests.post(url, headers=headers, data=body.encode('utf-8'), timeout=Config.TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            if data.get('ResponseMetadata', {}).get('Error'):
                err = data['ResponseMetadata']['Error']
                return None, f'翻译失败: {err.get("Message", "未知错误")}'

            translations = data.get('TranslationList', [])
            result = [t.get('Translation', '') for t in translations]
            if len(result) != len(texts):
                return None, '翻译结果数量与请求不一致'
            return result, None
        except requests.exceptions.Timeout:
            return None, '机器翻译连接超时，请稍后重试'
        except requests.exceptions.HTTPError as e:
            return None, f'机器翻译请求失败: {str(e)}'
        except Exception as e:
            return None, f'机器翻译调用异常: {str(e)}'

    # ============ 火山内容安全（AK/SK 签名，需 AppId） ============
    def call_content_security(self, text, app_id, service='text_risk'):
        """调用火山内容安全文本审核。需控制台的审核资产 AppId。"""
        if not self.content_ak:
            return None, '内容安全 AK 未配置'
        try:
            signer = VolcSigner(self.content_ak, self.content_sk)
            host = 'content.volcengineapi.com'
            region = 'cn-north-1'
            svc = 'content'
            path = '/'
            query = {'Action': 'TextSliceRisk', 'Version': '2021-06-29'}
            parameters = json.dumps({'text': text}, ensure_ascii=False)
            body = json.dumps({
                'AppId': int(app_id),
                'Service': service,
                'Parameters': parameters,
            }, ensure_ascii=False)

            headers, query_string = signer.sign('POST', host, region, svc, path, query, body)
            url = f'https://{host}{path}' + (f'?{query_string}' if query_string else '')

            resp = requests.post(url, headers=headers, data=body.encode('utf-8'), timeout=Config.TIMEOUT)
            resp.raise_for_status()
            return resp.json(), None
        except requests.exceptions.Timeout:
            return None, '内容安全连接超时'
        except requests.exceptions.HTTPError as e:
            return None, f'内容安全请求失败: {str(e)}'
        except Exception as e:
            return None, f'内容安全调用异常: {str(e)}'
