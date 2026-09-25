-- ==============================================================================
-- KnowGuard 智能知识库管理平台数据库初始化脚本
-- Database: MySQL 8.0+ / utf8mb4 / InnoDB
-- Generated for Production & Development Baseline
-- ==============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `knowguard` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `knowguard`;

-- ----------------------------
-- Table structure for audit_logs
-- ----------------------------
DROP TABLE IF EXISTS `audit_logs`;
CREATE TABLE audit_logs (
	trace_id VARCHAR(64) NOT NULL COMMENT '全链路调用追踪号', 
	conversation_id VARCHAR(64) COMMENT '关联会话ID', 
	user_id INTEGER COMMENT '提问用户员工ID', 
	username VARCHAR(64) COMMENT '员工登录名/真实姓名', 
	employee_id VARCHAR(64) COMMENT '员工工号', 
	user_dept VARCHAR(64) COMMENT '归属部门名称', 
	user_role VARCHAR(64) COMMENT '用户角色名称', 
	query_text TEXT NOT NULL COMMENT '提问内容', 
	answer_snippet TEXT COMMENT '答复摘要', 
	recalled_chunk_ids JSON NOT NULL COMMENT '召回切片ID列表', 
	recalled_count INTEGER NOT NULL COMMENT '召回切片数', 
	allowed_chunk_ids JSON NOT NULL COMMENT '4D安全放行切片ID列表', 
	allowed_count INTEGER NOT NULL COMMENT '放行切片数', 
	restricted_chunk_ids JSON NOT NULL COMMENT '4D安全拦截受限切片ID列表', 
	restricted_count INTEGER NOT NULL COMMENT '受限切片数', 
	is_blocked BOOL NOT NULL COMMENT '是否触发越权拦截', 
	block_reason VARCHAR(64) COMMENT '拦截原因', 
	prompt_tokens INTEGER NOT NULL COMMENT 'Prompt Token 消耗', 
	completion_tokens INTEGER NOT NULL COMMENT 'Completion Token 消耗', 
	total_tokens INTEGER NOT NULL COMMENT '总 Token 消耗', 
	latency_ms FLOAT NOT NULL COMMENT '全链路响应延迟 (ms)', 
	evidence_chain JSON COMMENT '下钻证据链明细', 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for conversations
-- ----------------------------
DROP TABLE IF EXISTS `conversations`;
CREATE TABLE conversations (
	id VARCHAR(64) NOT NULL COMMENT '会话全局唯一标识 UUID', 
	user_id BIGINT NOT NULL COMMENT '归属员工用户 ID (多租户物理隔离键)', 
	title VARCHAR(128) NOT NULL COMMENT '会话显示标题', 
	message_count INTEGER NOT NULL COMMENT '当前会话累计消息数量', 
	is_active BOOL NOT NULL COMMENT '会话有效状态 (True 正常, False 软删除)', 
	is_deleted BOOL NOT NULL COMMENT '软删除标记兼容字段', 
	created_at DATETIME NOT NULL COMMENT '会话创建时间', 
	updated_at DATETIME NOT NULL COMMENT '会话最后活跃时间', 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for departments
-- ----------------------------
DROP TABLE IF EXISTS `departments`;
CREATE TABLE departments (
	name VARCHAR(64) NOT NULL COMMENT '部门名称', 
	code VARCHAR(64) NOT NULL COMMENT '部门唯一标识编码', 
	parent_id INTEGER COMMENT '父部门ID', 
	materialized_path VARCHAR(255) NOT NULL COMMENT '物化路径，如 /1/3/', 
	level INTEGER NOT NULL COMMENT '部门层级 (1-8 级)', 
	sort_order INTEGER NOT NULL COMMENT '排序序号', 
	leader_name VARCHAR(64) COMMENT '部门负责人', 
	phone VARCHAR(32) COMMENT '联系电话', 
	email VARCHAR(128) COMMENT '部门邮箱', 
	status BOOL NOT NULL COMMENT '启停用状态', 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES departments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for faq_candidates
-- ----------------------------
DROP TABLE IF EXISTS `faq_candidates`;
CREATE TABLE faq_candidates (
	cluster_id VARCHAR(64) NOT NULL, 
	cluster_count INTEGER NOT NULL, 
	suggested_question VARCHAR(512) NOT NULL, 
	suggested_answer TEXT, 
	confidence_score FLOAT NOT NULL, 
	sample_queries JSON NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for faqs
-- ----------------------------
DROP TABLE IF EXISTS `faqs`;
CREATE TABLE faqs (
	standard_question VARCHAR(512) NOT NULL, 
	standard_answer TEXT NOT NULL, 
	category VARCHAR(64) NOT NULL, 
	similar_questions JSON NOT NULL, 
	is_cached BOOL NOT NULL, 
	is_enabled BOOL NOT NULL, 
	hit_count INTEGER NOT NULL, 
	candidate_id INTEGER, 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for knowledge_gaps
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_gaps`;
CREATE TABLE knowledge_gaps (
	query_text VARCHAR(512) NOT NULL, 
	hit_count INTEGER NOT NULL, 
	user_id INTEGER, 
	reason VARCHAR(64) NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	first_seen_at DATETIME NOT NULL, 
	last_seen_at DATETIME NOT NULL, 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for knowledge_units
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_units`;
CREATE TABLE knowledge_units (
	title VARCHAR(255) NOT NULL COMMENT '知识文件标题/文档名', 
	file_type VARCHAR(64) NOT NULL COMMENT '文件类型 (pdf, markdown, txt)', 
	file_path VARCHAR(512) COMMENT '物理文件存储路径或对象存储 URI', 
	file_size INTEGER NOT NULL COMMENT '原始文件大小 (字节)', 
	file_hash VARCHAR(64) COMMENT '文件 SHA-256 哈希防重指纹', 
	category VARCHAR(128) NOT NULL COMMENT '知识分类', 
	status VARCHAR(32) NOT NULL COMMENT '资产解析状态 (PENDING / PARSING / CHUNKING / INDEXED / FAILED)', 
	chunk_count INTEGER NOT NULL COMMENT '切片总分块数', 
	error_message TEXT COMMENT '解析或向量化异常错误日志', 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for roles
-- ----------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE roles (
	name VARCHAR(64) NOT NULL COMMENT '角色名称', 
	code VARCHAR(64) NOT NULL COMMENT '角色编码', 
	description VARCHAR(255) COMMENT '角色描述', 
	is_system BOOL NOT NULL COMMENT '是否系统内置角色', 
	status BOOL NOT NULL COMMENT '启停用状态', 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for knowledge_chunks
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_chunks`;
CREATE TABLE knowledge_chunks (
	document_id INTEGER NOT NULL COMMENT '关联知识单元主表 ID', 
	chunk_index INTEGER NOT NULL COMMENT '切片序号 (0-based)', 
	content TEXT NOT NULL COMMENT '切片纯文本正文内容', 
	char_length INTEGER NOT NULL COMMENT '切片正文字符长度', 
	status VARCHAR(32) NOT NULL COMMENT '切片向量化状态 (pending: 待入库 / indexed: 已同步 Milvus / failed: 失败)', 
	metadata_json JSON COMMENT '切片元数据 (如 start_pos, end_pos, page_no, chunk_id)', 
	has_vector BOOL NOT NULL COMMENT '是否已成功生成并在 Milvus 建库向量', 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES knowledge_units (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for messages
-- ----------------------------
DROP TABLE IF EXISTS `messages`;
CREATE TABLE messages (
	id BIGINT NOT NULL COMMENT '消息自增主键 ID' AUTO_INCREMENT, 
	conversation_id VARCHAR(64) NOT NULL COMMENT '所属会话全局唯一 ID', 
	`role` VARCHAR(16) NOT NULL COMMENT '消息角色: user / assistant / system', 
	content TEXT NOT NULL COMMENT '对话正文', 
	citations JSON COMMENT '4D 知识切片溯源引用列表 (JSON)', 
	is_silent_fallback BOOL NOT NULL COMMENT '是否触发了4D越权静默回退兜底', 
	status VARCHAR(20) NOT NULL COMMENT '消息状态: streaming | done | error', 
	created_at DATETIME NOT NULL COMMENT '消息产生时间', 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for permission_policies
-- ----------------------------
DROP TABLE IF EXISTS `permission_policies`;
CREATE TABLE permission_policies (
	unit_id INTEGER NOT NULL COMMENT '关联知识单元主表 ID', 
	is_public BOOL NOT NULL COMMENT '是否全员公开 (True 则跳过部门/角色/个人检查)', 
	department_ids JSON NOT NULL COMMENT '授权部门 ID 列表 (JSON Array)', 
	role_ids JSON NOT NULL COMMENT '授权角色 ID 列表 (JSON Array)', 
	user_ids JSON NOT NULL COMMENT '授权特定员工用户 ID 列表 (JSON Array)', 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(unit_id) REFERENCES knowledge_units (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for role_permissions
-- ----------------------------
DROP TABLE IF EXISTS `role_permissions`;
CREATE TABLE role_permissions (
	role_id INTEGER NOT NULL, 
	permission_code VARCHAR(64) NOT NULL COMMENT '权限唯一标识', 
	permission_type VARCHAR(32) NOT NULL COMMENT '权限分类: menu/route/button', 
	name VARCHAR(64) NOT NULL COMMENT '权限名称', 
	resource_path VARCHAR(128) COMMENT '前端路由或后端API路径', 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE users (
	employee_id VARCHAR(32) NOT NULL COMMENT '工号，如 10086', 
	username VARCHAR(64) NOT NULL COMMENT '登录用户名', 
	real_name VARCHAR(64) NOT NULL COMMENT '员工真实姓名', 
	hashed_password VARCHAR(255) NOT NULL COMMENT 'Bcrypt 工作因子 12 密文', 
	email VARCHAR(128) COMMENT '企业邮箱', 
	phone VARCHAR(32) COMMENT '联系手机', 
	avatar VARCHAR(255) COMMENT '头像URL', 
	department_id INTEGER COMMENT '所属部门ID', 
	is_active BOOL NOT NULL COMMENT '账号状态: 1正常 0禁用', 
	is_superuser BOOL NOT NULL COMMENT '是否超级管理员', 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(department_id) REFERENCES departments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for user_roles
-- ----------------------------
DROP TABLE IF EXISTS `user_roles`;
CREATE TABLE user_roles (
	user_id INTEGER NOT NULL, 
	role_id INTEGER NOT NULL, 
	id INTEGER NOT NULL AUTO_INCREMENT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_deleted BOOL NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- 初始系统基础与业务种子数据 (Seed Data)
-- ==============================================================================

BEGIN;

-- Records for departments (6 rows)
INSERT INTO `departments` (`name`, `code`, `parent_id`, `materialized_path`, `level`, `sort_order`, `leader_name`, `phone`, `email`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('管理层', 'DEPT_MGMT', NULL, '/1/', 1, 0, '王五', NULL, NULL, 1, 1, '2026-09-24 06:45:31.296270', '2026-09-24 06:45:31.296855', 0);
INSERT INTO `departments` (`name`, `code`, `parent_id`, `materialized_path`, `level`, `sort_order`, `leader_name`, `phone`, `email`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('研发部', 'DEPT_RD', 1, '/1/2/', 2, 0, '技术负责人', NULL, NULL, 1, 2, '2026-09-24 06:45:31.297255', '2026-09-24 06:45:31.297420', 0);
INSERT INTO `departments` (`name`, `code`, `parent_id`, `materialized_path`, `level`, `sort_order`, `leader_name`, `phone`, `email`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('财务部', 'DEPT_FINANCE', 1, '/1/3/', 2, 0, '李四', NULL, NULL, 1, 3, '2026-09-24 06:45:31.297760', '2026-09-24 06:45:31.297942', 0);
INSERT INTO `departments` (`name`, `code`, `parent_id`, `materialized_path`, `level`, `sort_order`, `leader_name`, `phone`, `email`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('算法部', 'DEPT_605088', NULL, '/4/', 1, 0, NULL, NULL, NULL, 1, 4, '2026-09-24 17:06:45.100809', '2026-09-24 17:06:45.102527', 0);
INSERT INTO `departments` (`name`, `code`, `parent_id`, `materialized_path`, `level`, `sort_order`, `leader_name`, `phone`, `email`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('工程部', 'DEPT_618643', 4, '/4/5/', 2, 0, NULL, NULL, NULL, 1, 5, '2026-09-24 17:06:58.652116', '2026-09-24 17:06:58.653290', 0);
INSERT INTO `departments` (`name`, `code`, `parent_id`, `materialized_path`, `level`, `sort_order`, `leader_name`, `phone`, `email`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('质量保障部', 'DEPT_026461', NULL, '/6/', 1, 0, NULL, NULL, NULL, 1, 6, '2026-09-24 18:53:46.472285', '2026-09-24 18:53:46.473870', 0);

-- Records for roles (6 rows)
INSERT INTO `roles` (`name`, `code`, `description`, `is_system`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('超级管理员', 'ROLE_SUPER_ADMIN', '拥有系统全量控制权限、组织架构管理、系统底层密钥与审计配置', 1, 1, 1, '2026-09-24 06:45:31.288993', '2026-09-24 06:45:31.288996', 0);
INSERT INTO `roles` (`name`, `code`, `description`, `is_system`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('知识管理员', 'ROLE_KNOWLEDGE_ADMIN', '负责知识库维护、文档导入切片、向量重构与知识自进化', 1, 1, 2, '2026-09-24 06:45:31.293117', '2026-09-24 18:55:02.640101', 0);
INSERT INTO `roles` (`name`, `code`, `description`, `is_system`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('普通员工', 'ROLE_COMMON_USER', '仅具备问答工作台、个人历史会话及放行知识查阅权限', 1, 1, 3, '2026-09-24 06:45:31.293495', '2026-09-24 06:45:31.293496', 0);
INSERT INTO `roles` (`name`, `code`, `description`, `is_system`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('HRBP', 'ROLE_HRBP', '具备人力行政知识管理、部门员工权限协同权限', 1, 1, 4, '2026-09-24 06:45:31.294385', '2026-09-24 06:45:31.294385', 0);
INSERT INTO `roles` (`name`, `code`, `description`, `is_system`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('部门经理', 'ROLE_DEPT_MANAGER', '负责部门日常运营管理与审批', 1, 1, 5, '2026-09-24 06:45:31.294713', '2026-09-24 06:45:31.294713', 0);
INSERT INTO `roles` (`name`, `code`, `description`, `is_system`, `status`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('合规审计员', 'ROLE_AUDITOR', '负责安全审计日志调阅、合规拦截监控与风险态势感知', 1, 1, 6, '2026-09-24 06:45:31.295034', '2026-09-24 06:45:31.295034', 0);

-- Records for role_permissions (51 rows)
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:menu', 'menu', '系统管理', '/admin/system', 1, '2026-09-24 06:45:31.289948', '2026-09-24 06:45:31.289949', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:dept:view', 'route', '部门架构管理', '/admin/system/departments', 2, '2026-09-24 06:45:31.289949', '2026-09-24 06:45:31.289950', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:dept:create', 'button', '新增部门', 'POST /api/v1/departments', 3, '2026-09-24 06:45:31.289950', '2026-09-24 06:45:31.289950', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:dept:update', 'button', '修改部门', 'PUT /api/v1/departments/*', 4, '2026-09-24 06:45:31.289951', '2026-09-24 06:45:31.289951', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:dept:delete', 'button', '删除部门', 'DELETE /api/v1/departments/*', 5, '2026-09-24 06:45:31.289951', '2026-09-24 06:45:31.289951', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:user:view', 'route', '员工账号管理', '/admin/system/users', 6, '2026-09-24 06:45:31.289951', '2026-09-24 06:45:31.289951', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:user:create', 'button', '新增员工', 'POST /api/v1/users', 7, '2026-09-24 06:45:31.289952', '2026-09-24 06:45:31.289952', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:user:update', 'button', '修改员工', 'PUT /api/v1/users/*', 8, '2026-09-24 06:45:31.289952', '2026-09-24 06:45:31.289952', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:user:status', 'button', '启停员工账号', 'PATCH /api/v1/users/*/status', 9, '2026-09-24 06:45:31.289952', '2026-09-24 06:45:31.289953', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:role:view', 'route', '角色与权限策略', '/admin/system/roles', 10, '2026-09-24 06:45:31.289953', '2026-09-24 06:45:31.289953', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:role:update', 'button', '配置角色权限', 'PUT /api/v1/roles/*/permissions', 11, '2026-09-24 06:45:31.289953', '2026-09-24 06:45:31.289953', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'system:role:assign', 'button', '分配用户角色', 'POST /api/v1/users/*/roles', 12, '2026-09-24 06:45:31.289954', '2026-09-24 06:45:31.289954', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'knowledge:menu', 'menu', '知识资产管理', '/admin/knowledge', 13, '2026-09-24 06:45:31.289954', '2026-09-24 06:45:31.289954', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'knowledge:view', 'route', '资产检索与台账列表', '/admin/knowledge/units', 14, '2026-09-24 06:45:31.289954', '2026-09-24 06:45:31.289954', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'knowledge:import', 'button', '批量导入与文档上传', 'POST /api/v1/knowledge/upload', 15, '2026-09-24 06:45:31.289955', '2026-09-24 06:45:31.289955', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'knowledge:reparse', 'button', '分词切片重析与向量化', 'POST /api/v1/knowledge/*/reparse', 16, '2026-09-24 06:45:31.289955', '2026-09-24 06:45:31.289955', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'knowledge:delete', 'button', '物理删除销毁知识资产', 'DELETE /api/v1/knowledge/*', 17, '2026-09-24 06:45:31.289955', '2026-09-24 06:45:31.289955', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'evolution:menu', 'menu', '知识自进化中心', '/admin/evolution', 18, '2026-09-24 06:45:31.289956', '2026-09-24 06:45:31.289956', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'evolution:view', 'route', '缺口清单与聚类审核', '/admin/evolution/gaps', 19, '2026-09-24 06:45:31.289956', '2026-09-24 06:45:31.289956', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'evolution:ticket:create', 'button', '知识缺口转建工单派发', 'POST /api/v1/evolution/tickets', 20, '2026-09-24 06:45:31.289956', '2026-09-24 06:45:31.289956', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'faq:publish', 'button', 'FAQ 审核与一键发布沉淀', 'POST /api/v1/evolution/faqs/publish', 21, '2026-09-24 06:45:31.289957', '2026-09-24 06:45:31.289957', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'analytics:menu', 'menu', '运营监控与审计大盘', '/admin/analytics', 22, '2026-09-24 06:45:31.289957', '2026-09-24 06:45:31.289957', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'analytics:view', 'route', '问答监控与KPI大盘查阅', '/admin/analytics/dashboard', 23, '2026-09-24 06:45:31.289957', '2026-09-24 06:45:31.289957', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'audit:export', 'button', '导出审计流水存证报告', 'POST /api/v1/analytics/audit/export', 24, '2026-09-24 06:45:31.289958', '2026-09-24 06:45:31.289958', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'chat:menu', 'menu', 'AI 智能问答工作台', '/chat', 25, '2026-09-24 06:45:31.289958', '2026-09-24 06:45:31.289958', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'chat:view', 'route', '问答工作台访问', '/chat', 26, '2026-09-24 06:45:31.289958', '2026-09-24 06:45:31.289958', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'chat:send', 'button', '发起提问与SSE交互', 'POST /api/v1/chat/completions', 27, '2026-09-24 06:45:31.289959', '2026-09-24 06:45:31.289959', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 'chat:feedback', 'button', '问答反馈打标', 'POST /api/v1/chat/feedback', 28, '2026-09-24 06:45:31.289959', '2026-09-24 06:45:31.289959', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (3, 'chat:menu', 'menu', 'AI 智能问答工作台', '/chat', 29, '2026-09-24 06:45:31.293738', '2026-09-24 06:45:31.293739', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (3, 'chat:view', 'route', '问答工作台访问', '/chat', 30, '2026-09-24 06:45:31.293739', '2026-09-24 06:45:31.293739', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (3, 'chat:send', 'button', '发起提问与SSE交互', 'POST /api/v1/chat/completions', 31, '2026-09-24 06:45:31.293739', '2026-09-24 06:45:31.293740', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (3, 'chat:feedback', 'button', '问答反馈打标', 'POST /api/v1/chat/feedback', 32, '2026-09-24 06:45:31.293740', '2026-09-24 06:45:31.293740', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (7, 'chat:menu', 'menu', 'AI 智能问答工作台', '/chat', 33, '2026-09-24 13:11:38.576921', '2026-09-24 13:11:38.576922', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (7, 'chat:view', 'route', '问答工作台访问', '/chat', 34, '2026-09-24 13:11:38.576923', '2026-09-24 13:11:38.576923', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (7, 'chat:send', 'button', '发起提问与SSE交互', 'POST /api/v1/chat/completions', 35, '2026-09-24 13:11:38.576923', '2026-09-24 13:11:38.576923', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (7, 'chat:feedback', 'button', '问答反馈打标', 'POST /api/v1/chat/feedback', 36, '2026-09-24 13:11:38.576924', '2026-09-24 13:11:38.576924', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'knowledge:menu', 'menu', '知识资产管理', '/admin/knowledge', 37, '2026-09-24 19:11:21.252067', '2026-09-24 19:11:21.252071', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'knowledge:view', 'route', '资产检索与台账列表', '/admin/knowledge/units', 38, '2026-09-24 19:11:21.252072', '2026-09-24 19:11:21.252072', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'knowledge:import', 'button', '批量导入与文档上传', 'POST /api/v1/knowledge/upload', 39, '2026-09-24 19:11:21.252073', '2026-09-24 19:11:21.252073', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'knowledge:reparse', 'button', '分词切片重析与向量化', 'POST /api/v1/knowledge/*/reparse', 40, '2026-09-24 19:11:21.252073', '2026-09-24 19:11:21.252073', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'knowledge:delete', 'button', '物理删除销毁知识资产', 'DELETE /api/v1/knowledge/*', 41, '2026-09-24 19:11:21.252074', '2026-09-24 19:11:21.252074', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'evolution:menu', 'menu', '知识自进化中心', '/admin/evolution', 42, '2026-09-24 19:11:21.252074', '2026-09-24 19:11:21.252074', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'evolution:view', 'route', '缺口清单与聚类审核', '/admin/evolution/gaps', 43, '2026-09-24 19:11:21.252074', '2026-09-24 19:11:21.252075', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'evolution:ticket:create', 'button', '知识缺口转建工单派发', 'POST /api/v1/evolution/tickets', 44, '2026-09-24 19:11:21.252075', '2026-09-24 19:11:21.252075', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'faq:publish', 'button', 'FAQ 审核与一键发布沉淀', 'POST /api/v1/evolution/faqs/publish', 45, '2026-09-24 19:11:21.252075', '2026-09-24 19:11:21.252075', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'analytics:menu', 'menu', '运营监控与审计大盘', '/admin/analytics', 46, '2026-09-24 19:11:21.252076', '2026-09-24 19:11:21.252076', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'analytics:view', 'route', '问答监控与KPI大盘查阅', '/admin/analytics/dashboard', 47, '2026-09-24 19:11:21.252076', '2026-09-24 19:11:21.252076', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'chat:menu', 'menu', 'AI 智能问答工作台', '/chat', 48, '2026-09-24 19:11:21.252076', '2026-09-24 19:11:21.252077', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'chat:view', 'route', '问答工作台访问', '/chat', 49, '2026-09-24 19:11:21.252077', '2026-09-24 19:11:21.252077', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'chat:send', 'button', '发起提问与SSE交互', 'POST /api/v1/chat/completions', 50, '2026-09-24 19:11:21.252077', '2026-09-24 19:11:21.252077', 0);
INSERT INTO `role_permissions` (`role_id`, `permission_code`, `permission_type`, `name`, `resource_path`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 'chat:feedback', 'button', '问答反馈打标', 'POST /api/v1/chat/feedback', 51, '2026-09-24 19:11:21.252078', '2026-09-24 19:11:21.252078', 0);

-- Records for users (4 rows)
INSERT INTO `users` (`employee_id`, `username`, `real_name`, `hashed_password`, `email`, `phone`, `avatar`, `department_id`, `is_active`, `is_superuser`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('10086', 'zhangsan', '张三', '$2b$12$hWiVLkiKaF.MDLOm4U/b4OuTNC/HY.P5PWl4IM54uYfW3MtCAr5Yq', NULL, NULL, NULL, 2, 1, 0, 1, '2026-09-24 06:45:31.466485', '2026-09-24 13:11:38.756189', 0);
INSERT INTO `users` (`employee_id`, `username`, `real_name`, `hashed_password`, `email`, `phone`, `avatar`, `department_id`, `is_active`, `is_superuser`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('10087', 'lisi', '李四', '$2b$12$EPxsudIeLYwJ2TiR7HbQoOnb61hFjb9Q9Bucm5PFHALjaPYdGKIW2', NULL, NULL, NULL, 3, 1, 0, 2, '2026-09-24 06:45:31.632826', '2026-09-24 13:11:38.925289', 0);
INSERT INTO `users` (`employee_id`, `username`, `real_name`, `hashed_password`, `email`, `phone`, `avatar`, `department_id`, `is_active`, `is_superuser`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('10088', 'wangwu', '王五', '$2b$12$hEdCHLYj8hv9kLPcigCFtOHnWr0xmFaotQrpuV.24jjMc8KFqUrMm', NULL, NULL, NULL, 1, 1, 1, 3, '2026-09-24 06:45:31.799906', '2026-09-24 13:11:39.093110', 0);
INSERT INTO `users` (`employee_id`, `username`, `real_name`, `hashed_password`, `email`, `phone`, `avatar`, `department_id`, `is_active`, `is_superuser`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('10609', 'lixi', 'lixi', '$2b$12$8BTxfBmQXcNgXr3m9WI7CuAntm9.xHdYk.uZ2p7Bzw5M0ijQx0XPS', NULL, NULL, NULL, 1, 0, 0, 4, '2026-09-24 17:06:25.708205', '2026-09-24 19:45:14.397801', 0);

-- Records for user_roles (4 rows)
INSERT INTO `user_roles` (`user_id`, `role_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 3, 4, '2026-09-24 13:11:38.757802', '2026-09-24 13:11:38.757803', 0);
INSERT INTO `user_roles` (`user_id`, `role_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (3, 1, 6, '2026-09-24 13:11:39.093648', '2026-09-24 13:11:39.093649', 0);
INSERT INTO `user_roles` (`user_id`, `role_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (4, 2, 7, '2026-09-24 17:06:25.708942', '2026-09-24 17:06:25.708943', 0);
INSERT INTO `user_roles` (`user_id`, `role_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 2, 8, '2026-09-24 19:11:21.254187', '2026-09-24 19:11:21.254189', 0);

-- Records for knowledge_units (3 rows)
INSERT INTO `knowledge_units` (`title`, `file_type`, `file_path`, `file_size`, `file_hash`, `category`, `status`, `chunk_count`, `error_message`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('01_企业通用差旅报销制度.md', 'markdown', NULL, 1336, '50ceabc57248349e8e7cd7d5277ba33b4067c5e82ec263ae245ffa576e7c91ee', 'TECH', 'INDEXED', 2, NULL, 1, '2026-09-24 16:54:15.529653', '2026-09-24 16:54:16.443245', 0);
INSERT INTO `knowledge_units` (`title`, `file_type`, `file_path`, `file_size`, `file_hash`, `category`, `status`, `chunk_count`, `error_message`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('02_研发中心Git与发布规范.txt', 'txt', NULL, 1155, 'efc78fe4791b902291250cbee22f4919765ab68ddbeff0f3f5a4ee9480ea6e3b', 'TECH', 'INDEXED', 2, NULL, 2, '2026-09-24 16:54:16.445022', '2026-09-24 16:54:16.681875', 0);
INSERT INTO `knowledge_units` (`title`, `file_type`, `file_path`, `file_size`, `file_hash`, `category`, `status`, `chunk_count`, `error_message`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('03_核心高管期权与激励方案.docx', 'docx', NULL, 37324, 'a37ecdaecd7cd23c2abb62f4618829310b9cbdaea0d44b5703223c3d0065c1c7', 'TECH', 'INDEXED', 1, NULL, 3, '2026-09-24 16:54:16.720368', '2026-09-24 16:54:17.035138', 0);

-- Records for knowledge_chunks (5 rows)
INSERT INTO `knowledge_chunks` (`document_id`, `chunk_index`, `content`, `char_length`, `status`, `metadata_json`, `has_vector`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 0, '# 企业通用差旅报销与补贴管理规范

## 1. 适用范围
本管理办法适用于全集团所有正式员工，包括试用期员工及实习生。所有因公出差事项均须严格遵守本办法。

## 2. 住宿标准上限
员工因公出差，每日住宿费用报销实行分类限额标准：
- **一类城市（北京、上海、广州、深圳）**：标准上限为 **600 元/天**。
- **二类城市（各省会城市、新一线城市、直辖市及副省级城市）**：标准上限为 **450 元/天**。
- **三类及其他城市**：标准上限为 **350 元/天**。
超标部分由员工个人自行承担，特殊业务情况须由部门总监提前书面审批。

## 3. 伙食与交通补贴
- **伙食补助**：包干标准为 **120 元/天**，按自然出差天数计发，无须提供发票。
- **市内公共交通补助**：包干标准为 **80 元/天**，含地铁、公交与网约车费用。
- **跨城交通**：高铁优先选择二等座；航程超过 4 小时或跨国出差经审批可乘坐普通舱。

## 4. 报销时效与流程
- 出差人员须在出差行程结束后 **15 个工作日内** 登录 OA 费用审批中心，填报《国内差旅报销单》。
- 必须附带增', 512, 'indexed', '{"start_idx": 0, "end_idx": 512, "file_name": "01_\u4f01\u4e1a\u901a\u7528\u5dee\u65c5\u62a5\u9500\u5236\u5ea6.md"}', 1, 1, '2026-09-24 16:54:15.532393', '2026-09-24 16:54:16.443843', 0);
INSERT INTO `knowledge_chunks` (`document_id`, `chunk_index`, `content`, `char_length`, `status`, `metadata_json`, `has_vector`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 1, '程
- 出差人员须在出差行程结束后 **15 个工作日内** 登录 OA 费用审批中心，填报《国内差旅报销单》。
- 必须附带增值税专用发票（或普通发票）、航空运输电子客票行程单或铁路车票原件。', 97, 'indexed', '{"start_idx": 448, "end_idx": 545, "file_name": "01_\u4f01\u4e1a\u901a\u7528\u5dee\u65c5\u62a5\u9500\u5236\u5ea6.md"}', 1, 2, '2026-09-24 16:54:15.532400', '2026-09-24 16:54:16.443845', 0);
INSERT INTO `knowledge_chunks` (`document_id`, `chunk_index`, `content`, `char_length`, `status`, `metadata_json`, `has_vector`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 0, '研发中心技术架构与Git分支规范

一、代码仓库分支模型
1. main 分支：生产环境绝对受保护分支，仅允许合规发布窗口由发布主管合并。
2. dev 分支：核心研发集成分支，每日自动触发 CI/CD 单元测试与代码质量门禁。
3. feature/* 分支：业务功能分支，由各研发工程师基于 dev 拉取开发，完成后提交 Merge Request。
4. hotfix/* 分支：生产紧急缺陷修复分支，基于 main 分支拉取，修复后必须同时同步合回 main 与 dev。

二、代码提交与代码审查规范
1. Commit Message 必须遵守 Conventional Commits 格式，例如：feat: 新增切片检索功能。
2. 每个 Merge Request 必须至少由 2 位同组资深工程师完成 Code Review 并在 GitLab 标记 Approve。
3. 单元测试行覆盖率不得低于 85%，核心鉴权安全逻辑必须达到 100% 覆盖。

三、生产发布与外发红线
1. 每周四为常规发版窗口日，禁止在周五及节假日前夕执行重大版本变更。
2. 严禁私自将包含企业密钥、数据库连接串或加密私钥', 512, 'indexed', '{"start_idx": 0, "end_idx": 512, "file_name": "02_\u7814\u53d1\u4e2d\u5fc3Git\u4e0e\u53d1\u5e03\u89c4\u8303.txt"}', 1, 3, '2026-09-24 16:54:16.445387', '2026-09-24 16:54:16.682269', 0);
INSERT INTO `knowledge_chunks` (`document_id`, `chunk_index`, `content`, `char_length`, `status`, `metadata_json`, `has_vector`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (2, 1, '线
1. 每周四为常规发版窗口日，禁止在周五及节假日前夕执行重大版本变更。
2. 严禁私自将包含企业密钥、数据库连接串或加密私钥的代码提交至外网或任何公开平台。', 80, 'indexed', '{"start_idx": 448, "end_idx": 528, "file_name": "02_\u7814\u53d1\u4e2d\u5fc3Git\u4e0e\u53d1\u5e03\u89c4\u8303.txt"}', 1, 4, '2026-09-24 16:54:16.445388', '2026-09-24 16:54:16.682271', 0);
INSERT INTO `knowledge_chunks` (`document_id`, `chunk_index`, `content`, `char_length`, `status`, `metadata_json`, `has_vector`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (3, 0, '2026年度核心高管中长期股权与期权激励方案

【密级：绝密 · 仅限董事会及核心高管人员查阅】

一、激励对象与授予资格

本方案激励对象仅限集团副总裁（VP）、首席技术官（CTO）、首席财务官（CFO）及以上级别核心经营管理层人员。经薪酬委员会提名并经董事会全票通过方可获得授予。

二、期权总量与行权价格

本期期权池总计预留 5,000,000 股普通股，占公司总股本的 5%。期权行权价格确定为每股人民币 12.50 元。

三、归属周期与解锁条件（Vesting Schedule）

期权授予后自次年起分 4 年匀速解锁归属：

1. 第 1 年（服务满 12 个月且年度 KPI 达到 A）：归属 25%；

2. 第 2 年（服务满 24 个月且年度营收增长率达到 30%）：归属 25%；

3. 第 3 年与第 4 年：分别归属 25%。若中途离职或触发竞业限制，未归属期权全额自动作废注销。', 407, 'indexed', '{"start_idx": 0, "end_idx": 407, "file_name": "03_\u6838\u5fc3\u9ad8\u7ba1\u671f\u6743\u4e0e\u6fc0\u52b1\u65b9\u6848.docx"}', 1, 5, '2026-09-24 16:54:16.720976', '2026-09-24 16:54:17.035607', 0);

-- Records for permission_policies (2 rows)
INSERT INTO `permission_policies` (`unit_id`, `is_public`, `department_ids`, `role_ids`, `user_ids`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (1, 1, '[]', '[]', '[]', 1, '2026-09-24 16:55:04.802651', '2026-09-24 16:55:04.802656', 0);
INSERT INTO `permission_policies` (`unit_id`, `is_public`, `department_ids`, `role_ids`, `user_ids`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES (3, 0, '[]', '[1, 2]', '[]', 2, '2026-09-24 17:12:05.579855', '2026-09-24 17:12:05.579863', 0);

-- Records for faqs (6 rows)
INSERT INTO `faqs` (`standard_question`, `standard_answer`, `category`, `similar_questions`, `is_cached`, `is_enabled`, `hit_count`, `candidate_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('什么是 KnowGuard 企业知识治理平台？', 'KnowGuard 是一站式企业级自进化知识库与智能问答安全网关平台，提供文档解析、多层权限隔离、实时意图防护、语义聚类挖掘与前置高速缓存等全栈能力。', '产品介绍', '["KnowGuard \u662f\u5e72\u4ec0\u4e48\u7684", "\u5e73\u53f0\u6838\u5fc3\u529f\u80fd\u6709\u54ea\u4e9b", "\u4ea7\u54c1\u5b9a\u4f4d"]', 1, 1, 1284, NULL, 1, '2026-09-24 17:57:38.732645', '2026-09-24 17:57:38.732649', 0);
INSERT INTO `faqs` (`standard_question`, `standard_answer`, `category`, `similar_questions`, `is_cached`, `is_enabled`, `hit_count`, `candidate_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('企业年金缴纳基数与比例如何计算？', '企业年金按上年度员工月均工资基数缴纳，企业缴存比例为 4%，员工个人缴存比例为 1.5%，按月直接汇缴至受托托管账户。', '薪酬福利', '["\u5e74\u91d1\u6263\u591a\u5c11", "\u516c\u53f8\u4ea4\u591a\u5c11\u5e74\u91d1", "\u5e74\u91d1\u6bd4\u4f8b"]', 1, 1, 896, NULL, 2, '2026-09-24 17:57:38.732650', '2026-09-24 17:57:38.732650', 0);
INSERT INTO `faqs` (`standard_question`, `standard_answer`, `category`, `similar_questions`, `is_cached`, `is_enabled`, `hit_count`, `candidate_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('跨国远程办公网络 VPN 客户端如何配置与登录？', '请从 IT 软件中心下载官方定制版 VPN 客户端，使用统一 LDAP 工号登录，并配合手机端动态两步认证（2FA）验证码完成鉴权。', 'IT运维', '["\u5916\u7f51\u8fde\u516c\u53f8\u5185\u7f51", "\u8fdc\u7a0b\u529e\u516cVPN", "VPN\u53cc\u56e0\u5b50\u8ba4\u8bc1"]', 1, 1, 672, NULL, 3, '2026-09-24 17:57:38.732650', '2026-09-24 17:57:38.732651', 0);
INSERT INTO `faqs` (`standard_question`, `standard_answer`, `category`, `similar_questions`, `is_cached`, `is_enabled`, `hit_count`, `candidate_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('跨境电商海关出口申报违禁品与限制出境物资目录？', '依据海关总署最新管制通告，禁止出境物品包括易燃易爆危化品、未经检疫动植物标本及国家限制外汇贵金属，详细目录见《出口管制物资分类索引2026版》。', '合规风控', '["\u51fa\u6d77\u54ea\u4e9b\u4e1c\u897f\u4e0d\u80fd\u53d1", "\u6e05\u5173\u8fdd\u7981\u54c1\u6e05\u5355", "\u51fa\u53e3\u53d7\u9650\u7269\u54c1"]', 0, 1, 451, NULL, 4, '2026-09-24 17:57:38.732651', '2026-09-24 17:57:38.732651', 0);
INSERT INTO `faqs` (`standard_question`, `standard_answer`, `category`, `similar_questions`, `is_cached`, `is_enabled`, `hit_count`, `candidate_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('企业专利发明与软著技术申报奖金激励政策？', '发明专利初审合格奖励 5,000 元，正式授权后奖励 15,000 元；软件著作权登记完成奖励 2,000 元。由技术委员会每季度统一评议公示并随薪发放。', '技术创新', '["\u53d1\u660e\u4e13\u5229\u5956\u52b1\u591a\u5c11", "\u8f6f\u8457\u7533\u8bf7\u5956\u91d1", "\u4e13\u5229\u8865\u8d34"]', 1, 1, 312, NULL, 5, '2026-09-24 17:57:38.732651', '2026-09-24 17:57:38.732652', 0);
INSERT INTO `faqs` (`standard_question`, `standard_answer`, `category`, `similar_questions`, `is_cached`, `is_enabled`, `hit_count`, `candidate_id`, `id`, `created_at`, `updated_at`, `is_deleted`) VALUES ('公积金异地转移与跨省封存接续操作指引？', '请在全国住房公积金微信小程序提交“转移接续”申请，填报转出地与转入地中心名称，系统将在 5 个工作日内自动办结资金划转。', 'DEFAULT', '["\u516c\u79ef\u91d1\u8f6c\u79fb", "\u516c\u79ef\u91d1\u600e\u4e48\u8f6c\u5916\u7701", "\u79bb\u804c\u516c\u79ef\u91d1\u5c01\u5b58"]', 1, 1, 0, 5, 6, '2026-09-24 18:56:05.318469', '2026-09-24 18:56:05.318471', 0);

COMMIT;

SET FOREIGN_KEY_CHECKS = 1;

-- ==============================================================================
-- End of KnowGuard Database Initialization Script
-- ==============================================================================
