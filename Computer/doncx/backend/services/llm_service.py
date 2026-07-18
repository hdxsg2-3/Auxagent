import json
from config import Config
from utils.api_client import APIClient
from services.prompt_manager import PromptManager
from utils.logger import log_error

class LLMService:
    def __init__(self):
        self.client = APIClient()
        self.prompt_manager = PromptManager()
        self.model_name = Config.MODEL_NAME
    
    def generate_text(self, prompt, model=None):
        messages = [{'role': 'user', 'content': prompt}]
        response, error = self.client.call_llm(messages, model=model or self.model_name)
        return response, error
    
    def generate_copywriter(self, product_desc, platform, target_language, auto_compliance=True):
        try:
            prompt = self.prompt_manager.get_copywriter_prompt(
                product_desc, platform, target_language
            )
            messages = [{'role': 'user', 'content': prompt}]
            response, error = self.client.call_llm(messages, model=self.model_name)
            
            if error:
                log_error('LLMService', f'Copywriter generate error: {error}')
                return {'error': error}
            
            if not response:
                return {'error': 'AI 未返回任何内容，请稍后重试'}
            
            result = self._parse_copywriter_response(response, target_language)
            compliance_scan = None
            compliance_info = {'original_clean': True, 'rewritten': False}

            if auto_compliance and not result.get('error'):
                combined = self._combine_copywriter_text(result)
                scan = self.scan_compliance(combined, True, True, True)
                if scan and not scan.get('error'):
                    compliance_scan = scan
                    if not scan.get('clean', True) or scan.get('overall_risk') in ('medium', 'high'):
                        compliance_info = {
                            'original_clean': False,
                            'original_overall_risk': scan.get('overall_risk', 'low'),
                            'notes': scan.get('suggestions', []) + self._compliance_issue_notes(scan),
                            'rewritten': True
                        }
                        rewrite_prompt = self.prompt_manager.get_rewrite_prompt(
                            result, scan, platform, target_language
                        )
                        rewrite_resp, rewrite_err = self.client.call_llm(
                            [{'role': 'user', 'content': rewrite_prompt}], model=self.model_name
                        )
                        if rewrite_resp and not rewrite_err:
                            rewritten = self._parse_copywriter_response(rewrite_resp, target_language)
                            if not rewritten.get('error'):
                                result = rewritten
                                # 改写后再次扫描最终文本，确保风控报告与成品完全一致
                                final_combined = self._combine_copywriter_text(result)
                                final_scan = self.scan_compliance(final_combined, True, True, True)
                                if final_scan and not final_scan.get('error'):
                                    compliance_scan = final_scan
                        else:
                            log_error('LLMService', f'Compliance rewrite error: {rewrite_err}')
                else:
                    err = scan.get('error') if scan else 'empty scan'
                    log_error('LLMService', f'Compliance scan during generation failed: {err}')

            # compliance_scan 供上游编排直接复用，避免重复 LLM 调用
            result['compliance_scan'] = compliance_scan
            result['compliance'] = compliance_info
            return result
        except Exception as e:
            log_error('LLMService', e)
            return {'error': f'生成文案时发生异常：{str(e)}'}
    
    def _parse_copywriter_response(self, response, target_language):
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                data = json.loads(json_str)
                return data
        except json.JSONDecodeError:
            pass
        
        return {
            'title': 'Generated Title',
            'bullet_points': [
                'Feature 1',
                'Feature 2',
                'Feature 3',
                'Feature 4',
                'Feature 5'
            ],
            'description': response
        }
    
    def _combine_copywriter_text(self, result):
        title = result.get('title', '')
        bullets = result.get('bullet_points', [])
        desc = result.get('description', '')
        return f'标题：{title}\n卖点：{"；".join(bullets)}\n描述：{desc}'
    
    def _compliance_issue_notes(self, scan):
        notes = []
        for item in scan.get('extreme_words', []):
            word = item.get('word', '')
            suggestion = item.get('suggestion', '')
            if word:
                notes.append(f'极限词：{word} -> {suggestion}')
        for item in scan.get('forbidden_words', []):
            word = item.get('word', '')
            category = item.get('category', '')
            if word:
                notes.append(f'违禁词：{word}（{category}）')
        return notes
    
    def refine_product_info(self, raw_text):
        try:
            prompt = self.prompt_manager.get_refine_prompt(raw_text)
            messages = [{'role': 'user', 'content': prompt}]
            response, error = self.client.call_llm(messages, model=self.model_name)

            if error:
                log_error('LLMService', f'Refine product info error: {error}')
                return {'error': error}

            if response:
                return self._parse_refine_response(response)
            return None
        except Exception as e:
            log_error('LLMService', e)
            return None

    def _parse_refine_response(self, response):
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                data = json.loads(response[start:end])
                data.setdefault('product_name', '')
                data.setdefault('core_selling_points', [])
                data.setdefault('key_parameters', [])
                data.setdefault('applicable_scenarios', [])
                data.setdefault('clean_description', '')
                return data
        except json.JSONDecodeError:
            pass

        return {'error': 'AI 返回内容无法解析，请重试'}

    def translate_copywriter(self, title, bullet_points, description, target_language):
        # 优先用火山机器翻译（更专业、更省大模型额度），失败回退大模型
        try:
            texts = [title] + list(bullet_points) + [description]
            translated, error = self.client.call_translate(texts, target_language)
            if translated and not error:
                return {
                    'title': translated[0],
                    'bullet_points': translated[1:1 + len(bullet_points)],
                    'description': translated[-1],
                }
            log_error('LLMService', f'Machine translate failed, fallback to LLM: {error}')
        except Exception as e:
            log_error('LLMService', f'Machine translate exception, fallback to LLM: {e}')

        # 回退：大模型翻译
        try:
            prompt = self.prompt_manager.get_translate_prompt(
                title, bullet_points, description, target_language
            )
            messages = [{'role': 'user', 'content': prompt}]
            response, error = self.client.call_llm(messages, model=self.model_name)
            
            if error:
                log_error('LLMService', f'Translate error: {error}')
                return {'error': error}
            
            if response:
                return self._parse_copywriter_response(response, target_language)
            return {'error': 'AI 未返回任何内容，请稍后重试'}
        except Exception as e:
            log_error('LLMService', e)
            return {'error': f'翻译文案时发生异常：{str(e)}'}
    
    def scan_compliance(self, content, check_extreme_words, check_copyright, check_forbidden_words):
        # 若配置了火山内容安全 AppId，优先走专用审核 API，失败回退大模型
        app_id = Config.VOLC_CONTENT_APP_ID
        if app_id:
            try:
                raw, error = self.client.call_content_security(content, app_id)
                if raw and not error:
                    mapped = self._map_content_security(raw)
                    if mapped:
                        return mapped
                log_error('LLMService', f'Content security failed, fallback to LLM: {error}')
            except Exception as e:
                log_error('LLMService', f'Content security exception, fallback to LLM: {e}')

        # 回退：大模型合规检测
        try:
            prompt = self.prompt_manager.get_compliance_prompt(
                content, check_extreme_words, check_copyright, check_forbidden_words
            )
            messages = [{'role': 'user', 'content': prompt}]
            response, error = self.client.call_llm(messages, model=self.model_name)
            
            if error:
                log_error('LLMService', f'Compliance scan error: {error}')
                return {'error': error}
            
            if response:
                return self._parse_compliance_response(response)
            return {'error': 'AI 未返回任何内容'}
        except Exception as e:
            log_error('LLMService', e)
            return {'error': f'合规检测异常：{str(e)}'}

    def _map_content_security(self, raw):
        """
        将火山内容安全返回结果映射为现有前端所需的合规结构。
        内容安全（businessSecurity）返回结构与当前前端字段不完全一致，
        需要真实响应样本才能精确映射，这里先做保守处理：
          - 能识别出明确风险等级时返回结构；否则返回 None 让上层回退大模型。
        待用户提供 AppId 与一次真实响应样本后，可在此精确映射。
        """
        try:
            data = raw.get('Data', raw)
            results = data.get('Results', []) if isinstance(data, dict) else []
            if not results:
                return None
            risk_level = str(results[0].get('RiskLevel', '')).lower()
            overall = 'low'
            if 'high' in risk_level or 'block' in risk_level:
                overall = 'high'
            elif 'mid' in risk_level or 'review' in risk_level:
                overall = 'medium'
            forbidden = []
            for r in results:
                label = r.get('RiskLabel1') or r.get('RiskLabel2') or ''
                if label:
                    forbidden.append({'word': label, 'category': r.get('RiskLabel2', '内容安全风险')})
            return {
                'overall_risk': overall,
                'extreme_words': [],
                'copyright_issues': [],
                'forbidden_words': forbidden,
                'clean': len(forbidden) == 0,
                'suggestions': ['内容安全检测到风险项，请核对后修改'] if forbidden else [],
            }
        except Exception:
            return None
    
    def _parse_compliance_response(self, response):
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                data = json.loads(json_str)
                return data
        except json.JSONDecodeError:
            pass
        
        return {
            'overall_risk': 'low',
            'extreme_words': [],
            'copyright_issues': [],
            'forbidden_words': [],
            'clean': True,
            'suggestions': []
        }
    
    def process_customer_service(self, message, platform):
        try:
            prompt = self.prompt_manager.get_customer_service_prompt(message, platform)
            messages = [{'role': 'user', 'content': prompt}]
            response, error = self.client.call_llm(messages, model=self.model_name)
            
            if error:
                log_error('LLMService', f'Customer service error: {error}')
                return {'error': error}
            
            if response:
                return self._parse_customer_service_response(response)
            return None
        except Exception as e:
            log_error('LLMService', e)
            return None
    
    def _parse_customer_service_response(self, response):
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                data = json.loads(json_str)
                data.setdefault('response', '')
                data.setdefault('response_zh', '')
                data.setdefault('status', 'auto_replied')
                return data
        except json.JSONDecodeError:
            pass
        
        return {
            'response': response,
            'response_zh': '',
            'status': 'auto_replied'
        }
    
    def search_legal(self, query, regions):
        try:
            prompt = self.prompt_manager.get_legal_search_prompt(query, regions)
            messages = [{'role': 'user', 'content': prompt}]
            response, error = self.client.call_llm(messages, model=self.model_name)
            
            if error:
                log_error('LLMService', f'Legal search error: {error}')
                return {'error': error}
            
            if response:
                return self._parse_legal_response(response)
            return None
        except Exception as e:
            log_error('LLMService', e)
            return None
    
    def _parse_legal_response(self, response):
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                data = json.loads(json_str)
                return data
        except json.JSONDecodeError:
            pass
        
        return []
