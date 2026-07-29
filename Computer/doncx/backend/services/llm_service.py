import json
import time
from config import Config
from utils.api_client import APIClient
from services.prompt_manager import PromptManager
from services.knowledge_base import KnowledgeBase
from utils.logger import log_error
from utils.db import add_invocation_log

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
            
            # 合规扫描按需触发：auto_compliance=True 才扫描并写入 result['compliance']
            # 默认 auto_compliance=False，前端可手动调用「合规扫描」按钮触发
            if auto_compliance and not result.get('error'):
                try:
                    combined = self._combine_copywriter_text(result)
                    scan = self.scan_compliance(combined, True, True, True)
                    if scan and not scan.get('error'):
                        result['compliance_scan'] = scan
                        if not scan.get('clean', True) or scan.get('overall_risk') in ('medium', 'high'):
                            result['compliance'] = {
                                'original_clean': False,
                                'original_overall_risk': scan.get('overall_risk', 'low'),
                                'notes': scan.get('suggestions', []) + self._compliance_issue_notes(scan),
                                'rewritten': False,
                                'risk': scan.get('overall_risk', 'medium'),
                                'hint': '检测到合规风险，请使用「合规改写」按钮手动触发改写'
                            }
                        else:
                            result['compliance'] = {
                                'original_clean': True,
                                'rewritten': False,
                                'risk': 'low',
                                'notes': []
                            }
                except Exception as scan_err:
                    log_error('LLMService', f'Compliance scan error (non-blocking): {scan_err}')

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

    def translate_manual_response(self, manual_reply, customer_message, platform):
        """
        将人工客服回复自动翻译成客户咨询使用的语言。
        返回 dict: {detected_language, language_name, translated_reply}
        """
        if not manual_reply or not manual_reply.strip():
            return {
                'detected_language': 'unknown',
                'language_name': '未知',
                'translated_reply': ''
            }
        try:
            prompt = self.prompt_manager.get_manual_reply_translate_prompt(
                manual_reply, customer_message, platform
            )
            messages = [{'role': 'user', 'content': prompt}]
            response, error = self.client.call_llm(messages, model=self.model_name)

            if error:
                log_error('LLMService', f'Manual reply translate error: {error}')
                return {
                    'detected_language': 'unknown',
                    'language_name': '未知',
                    'translated_reply': manual_reply,
                    'error': error
                }

            result = self._parse_manual_reply_translate_response(response)
            if result.get('translated_reply'):
                return result
            # 解析失败但想尽量兜底：返回原文
            return {
                'detected_language': 'unknown',
                'language_name': '未知',
                'translated_reply': manual_reply
            }
        except Exception as e:
            log_error('LLMService', e)
            return {
                'detected_language': 'unknown',
                'language_name': '未知',
                'translated_reply': manual_reply
            }

    def _parse_manual_reply_translate_response(self, response):
        """解析 LLM 返回的人工回复翻译结果"""
        if not response:
            return {}
        try:
            data = self._extract_first_json(response)
            if data and isinstance(data, dict):
                return {
                    'detected_language': data.get('detected_language', 'unknown'),
                    'language_name': data.get('language_name', '未知'),
                    'translated_reply': data.get('translated_reply', '')
                }
        except Exception:
            pass
        return {}

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
    
    def scan_compliance(self, content, check_extreme_words, check_copyright, check_forbidden_words, image_texts=''):
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
                content, check_extreme_words, check_copyright, check_forbidden_words, image_texts
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
    
    def process_customer_service(self, message, platform, merchant_id='default', buyer_id=''):
        """
        客服消息处理（RAG 增强版 + 买家历史上下文）

        流程：
        1. 检索该买家的历史对话（精确匹配 buyer_id）
        2. 检索知识库中相关条目（向量检索）
        3. 检索历史相似对话（向量检索，可能跨买家）
        4. 将三段检索结果注入 prompt
        5. 调用 LLM 生成回复
        6. 保存本轮对话到记忆库（附带 buyer_id）
        7. 写入调用历史记录
        """
        t0 = time.time()
        try:
            kb = KnowledgeBase(merchant_id)

            # Step 1-2: RAG 检索（含买家历史）
            retrieved = kb.search_knowledge(message, buyer_id=buyer_id)

            # 格式化知识库上下文
            knowledge_parts = []
            for item in retrieved.get('knowledge', []):
                knowledge_parts.append(
                    f"【{item['category_name']}】{item['title']}\n{item['content']}"
                )
            knowledge_context = '\n\n'.join(knowledge_parts) if knowledge_parts else ''

            # 格式化买家本人的历史对话
            buyer_history_parts = []
            for item in retrieved.get('buyer_history', []):
                buyer_history_parts.append(
                    f"客户问：{item['question']}\n回复：{item['response']}"
                )
            buyer_history_context = '\n\n'.join(buyer_history_parts) if buyer_history_parts else ''

            # 格式化语义检索到的同类对话（可能跨买家）
            memory_parts = []
            for item in retrieved.get('memories', []):
                memory_parts.append(
                    f"客户问：{item['question']}\n回复：{item['response']}"
                )
            memory_context = '\n\n'.join(memory_parts) if memory_parts else ''

            # Step 3: 用 RAG 增强 prompt（三段式）
            prompt = self.prompt_manager.get_rag_customer_service_prompt(
                message, platform, knowledge_context,
                memory_context, buyer_history_context
            )
            messages = [{'role': 'user', 'content': prompt}]
            response, error = self.client.call_llm(messages, model=self.model_name)

            latency_ms = int((time.time() - t0) * 1000)

            if error:
                log_error('LLMService', f'Customer service error: {error}')
                try:
                    add_invocation_log(merchant_id, platform, message, '',
                                       status='failed', latency_ms=latency_ms,
                                       model_name=self.model_name, buyer_id=buyer_id)
                except Exception:
                    pass
                return {'error': error}

            if response:
                result = self._parse_customer_service_response(response)

                # Step 5: 保存本轮对话到记忆库（附带买家标识，不阻塞）
                try:
                    kb.remember_conversation(message, result.get('response', ''), buyer_id)
                except Exception as mem_err:
                    log_error('LLMService', f'记忆保存失败: {mem_err}')

                # Step 6: 写入调用历史记录
                try:
                    add_invocation_log(merchant_id, platform, message,
                                       result.get('response', ''),
                                       status=result.get('status', 'success'),
                                       latency_ms=latency_ms,
                                       model_name=self.model_name,
                                       buyer_id=buyer_id)
                except Exception as log_err:
                    log_error('LLMService', f'调用历史写入失败: {log_err}')

                # Step 7: 自动品类归纳（每积累 15 轮对话触发一次，避免频繁调用 LLM）
                try:
                    from utils.db import list_conversation_memory as _list_mem
                    mem_count = len(_list_mem(merchant_id))
                    if mem_count > 0 and mem_count % 15 == 0:
                        print(f"[LLMService] 对话记忆已达 {mem_count} 条，自动触发品类归纳...")
                        kb.extract_product_categories()
                except Exception as cat_err:
                    log_error('LLMService', f'自动品类归纳失败: {cat_err}')

                # 附带检索结果供调试
                result['_retrieved'] = {
                    'knowledge_count': len(retrieved.get('knowledge', [])),
                    'memory_count': len(retrieved.get('memories', [])),
                    'buyer_history_count': len(retrieved.get('buyer_history', []))
                }
                result['_latency_ms'] = latency_ms
                return result
            return None
        except Exception as e:
            log_error('LLMService', e)
            return None
    
    def _extract_first_json(self, text):
        """从文本中提取第一个完整 JSON 对象（支持嵌套大括号）"""
        start = text.find('{')
        if start == -1:
            return None
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        return None
        return None

    def _parse_customer_service_response(self, response):
        if not response:
            return {
                'response': '',
                'response_zh': '',
                'status': 'auto_replied'
            }

        # 优先尝试完整解析（LLM 听话时直接就是干净 JSON）
        try:
            data = json.loads(response.strip())
            if isinstance(data, dict):
                data.setdefault('response', '')
                data.setdefault('response_zh', '')
                data.setdefault('status', 'auto_replied')
                return data
        except json.JSONDecodeError:
            pass

        # 提取第一个完整 JSON 对象，避免把多个 JSON 和解释文字混在一起
        data = self._extract_first_json(response)
        if data and isinstance(data, dict):
            data.setdefault('response', '')
            data.setdefault('response_zh', '')
            data.setdefault('status', 'auto_replied')
            return data

        # 兜底：把原始文本作为回复返回，避免前端空白
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
