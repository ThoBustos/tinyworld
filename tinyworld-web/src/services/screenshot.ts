import { Application } from 'pixi.js';

export class ScreenshotService {
  private app: Application;
  private captureInterval: number | null = null;
  private onScreenshotCallback: ((filePath: string) => void) | null = null;
  private isCapturing: boolean = false;
  
  constructor(app: Application) {
    this.app = app;
  }
  
  /**
   * Capture a screenshot and return as base64 data URL
   * @returns Base64 data URL of the screenshot
   */
  async captureScreenshot(): Promise<string> {
    try {
      // Extract base64 image from the renderer
      const base64 = await this.app.renderer.extract.base64(this.app.stage);
      
      console.log(`📸 Screenshot captured (size: ${Math.round(base64.length / 1024)}KB)`);
      return base64;
      
    } catch (error) {
      console.error('Failed to capture screenshot:', error);
      throw error;
    }
  }
  
  /**
   * Start capturing screenshots at regular intervals
   * @param intervalSeconds Interval between captures (default 30s)
   * @param onScreenshot Callback when screenshot is captured
   */
  startCapturing(intervalSeconds: number = 30, onScreenshot: (dataUrl: string) => void): void {
    if (this.isCapturing) {
      console.warn('Screenshot capturing already started');
      return;
    }
    
    this.onScreenshotCallback = onScreenshot;
    this.isCapturing = true;
    
    console.log(`🎬 Starting screenshot capture every ${intervalSeconds} seconds`);
    
    // Capture first screenshot immediately
    this.captureAndNotify();
    
    // Set up interval for subsequent captures
    this.captureInterval = window.setInterval(() => {
      this.captureAndNotify();
    }, intervalSeconds * 1000);
  }
  
  /**
   * Stop capturing screenshots
   */
  stopCapturing(): void {
    if (this.captureInterval) {
      clearInterval(this.captureInterval);
      this.captureInterval = null;
    }
    this.isCapturing = false;
    console.log('🛑 Stopped screenshot capture');
  }
  
  /**
   * Internal method to capture and notify
   */
  private async captureAndNotify(): Promise<void> {
    try {
      const dataUrl = await this.captureScreenshot();
      if (this.onScreenshotCallback) {
        this.onScreenshotCallback(dataUrl);
      }
    } catch (error) {
      console.error('Screenshot capture failed:', error);
      // Continue capturing even if one fails
    }
  }
  
}