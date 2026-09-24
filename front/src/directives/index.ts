/**
 * 全局自定义指令统一注册入口
 */

import type { App } from 'vue'
import { permissionDirective } from './permission'

export const setupDirectives = (app: App): void => {
  app.directive('permission', permissionDirective)
}
