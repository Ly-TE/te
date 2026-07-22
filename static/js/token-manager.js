/**
 * 统一Token管理模块
 * 负责与后端统一登录接口交互，管理token的获取、存储和续期
 */

class UnifiedTokenManager {
    constructor() {
        this.token = localStorage.getItem('unified_token') || '';
        this.expiryTime = localStorage.getItem('unified_token_expiry') || '';
        this.clientId = this.generateClientId();
    }
    
    /**
     * 生成客户端唯一标识
     */
    generateClientId() {
        // 基于浏览器指纹生成客户端ID
        const fingerprint = [
            navigator.userAgent,
            navigator.language,
            screen.width,
            screen.height,
            new Date().getTimezoneOffset()
        ].join('|');
        
        // 简单哈希算法
        let hash = 0;
        for (let i = 0; i < fingerprint.length; i++) {
            const char = fingerprint.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // 转换为32位整数
        }
        return 'client_' + Math.abs(hash).toString(36);
    }
    
    /**
     * 获取有效token
     * @returns {Promise<string|null>} token字符串或null
     */
    async getToken(forceRefresh = false) {
        // 如果强制刷新，直接获取新token
        if (forceRefresh) {
            console.log('[TokenManager] 强制刷新token');
            return await this.refreshToken();
        }
        
        // 检查本地token是否有效
        if (this.token && !this.isTokenExpired()) {
            console.log('[TokenManager] 使用缓存的token');
            return this.token;
        }
        
        // 从后端获取新token
        console.log('[TokenManager] 缓存token已过期，获取新token');
        return await this.refreshToken();
    }
    
    /**
     * 刷新token
     * @returns {Promise<string|null>} 新token或null
     */
    async refreshToken() {
        const newToken = await this.fetchTokenFromBackend();
        
        if (newToken) {
            this.token = newToken.token;
            this.expiryTime = newToken.expiry_time;
            
            // 保存到本地存储
            localStorage.setItem('unified_token', this.token);
            localStorage.setItem('unified_token_expiry', this.expiryTime);
            
            console.log('[TokenManager] Token刷新成功，有效期至:', this.expiryTime);
            return this.token;
        }
        
        console.error('[TokenManager] 刷新token失败');
        return null;
    }
    
    /**
     * 从后端获取token
     * @returns {Promise<Object|null>} token信息对象或null
     */
    async fetchTokenFromBackend() {
        try {
            const response = await fetch('/api/auth/token', {
                method: 'GET'  // Must use GET method as per API requirement
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.token) {
                return {
                    token: data.token,
                    expiry_time: data.expiry_time
                };
            } else {
                console.error('[TokenManager] 后端返回错误:', data.message);
                return null;
            }
            
        } catch (error) {
            console.error('[TokenManager] 获取token时发生网络错误:', error);
            return null;
        }
    }
    
    /**
     * 检查token是否过期（不使用缓冲时间，直接比较）
     * @returns {boolean} 是否过期
     */
    isTokenExpired() {
        if (!this.expiryTime) {
            return true;
        }
        
        try {
            let expiryDate;
            
            // 处理不同格式的时间字符串
            if (this.expiryTime.includes('T')) {
                // ISO格式: 2026-02-19T22:46:41
                expiryDate = new Date(this.expiryTime);
            } else if (this.expiryTime.includes(' ')) {
                // 自定义格式: 2026-02-19 22:46:41
                // 先转换为ISO格式再解析
                const isoFormat = this.expiryTime.replace(' ', 'T');
                expiryDate = new Date(isoFormat);
            } else {
                // 尝试直接解析
                expiryDate = new Date(this.expiryTime);
            }
            
            // 直接比较，不使用缓冲时间
            const result = Date.now() >= expiryDate.getTime();
            
            console.log(`[TokenManager] 时间检查 - 当前: ${new Date().toISOString()}, 过期: ${expiryDate.toISOString()}, 结果: ${result}`);
            
            return result;
        } catch (error) {
            console.error('[TokenManager] 解析过期时间失败:', error);
            return true;
        }
    }
    
    /**
     * 清除本地token
     */
    clearToken() {
        this.token = '';
        this.expiryTime = '';
        localStorage.removeItem('unified_token');
        localStorage.removeItem('unified_token_expiry');
        console.log('[TokenManager] 本地token已清除');
    }
    
    /**
     * 验证token有效性（轻量级探针）
     * @returns {Promise<boolean>} token是否有效
     */
    async validateToken() {
        try {
            const response = await fetch('/api/auth/token/validate', {
                method: 'GET'  // Must use GET method as per API requirement
            });
            
            if (!response.ok) {
                return false;
            }
            
            const data = await response.json();
            return data.success && data.valid;
            
        } catch (error) {
            console.error('[TokenManager] 验证token时发生错误:', error);
            return false;
        }
    }
    
    /**
     * 获取token统计信息（管理员功能）
     * @returns {Promise<Object|null>} 统计信息或null
     */
    async getTokenStats() {
        try {
            const response = await fetch('/api/auth/stats', {
                method: 'GET'  // Must use GET method as per API requirement
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data.success ? data.stats : null;
            
        } catch (error) {
            console.error('[TokenManager] 获取统计信息时发生错误:', error);
            return null;
        }
    }
}

// 创建全局实例
const tokenManager = new UnifiedTokenManager();

// 导出供其他模块使用
window.UnifiedTokenManager = UnifiedTokenManager;
window.tokenManager = tokenManager;