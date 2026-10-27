// One UiAutomation owner serves every named hidden display. No physical-screen input.
// Build against android.jar, then D8. Keep the accessibility-preservation flag.
import android.app.UiAutomation;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.os.Bundle;
import android.os.HandlerThread;
import android.os.Looper;
import android.util.SparseArray;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.lang.reflect.Constructor;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;

public class UD {
  static UiAutomation automation;
  static volatile boolean dirty = true;
  static final String epoch = Long.toHexString(System.currentTimeMillis()) + "-" + Long.toHexString(System.nanoTime());
  static final Map<String, Screen> screens = new LinkedHashMap<>();
  static class Screen {
    String name, fingerprint = "";
    int display;
    long revision = 0;
    File dir;
    JSONObject snapshot;
    Map<String, AccessibilityNodeInfo> nodes = new LinkedHashMap<>();
    Screen(String n, int d, File f) { name=n; display=d; dir=f; }
    String generation() { return epoch + ":" + display; }
  }
  static String text(CharSequence value) { return value == null ? "" : value.toString(); }
  static String xml(String s) {
    return s.replace("&","&amp;").replace("\"","&quot;").replace("<","&lt;").replace(">","&gt;").replace("\n"," ").replace("\r"," ");
  }
  static String read(File file) throws Exception { return new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8); }
  static void write(File file, String value) throws Exception {
    File tmp = new File(file.getPath()+".tmp");
    try (FileOutputStream stream = new FileOutputStream(tmp)) { stream.write(value.getBytes(StandardCharsets.UTF_8)); }
    if (!tmp.renameTo(file)) throw new IOException("atomic publish failed: " + file);
  }
  static void release(Screen screen) {
    for (AccessibilityNodeInfo node : screen.nodes.values()) { try { node.recycle(); } catch (Throwable ignored) {} }
    screen.nodes.clear();
  }
  static void connect() throws Exception {
    HandlerThread thread = new HandlerThread("agent-bridge-reader"); thread.start();
    Class<?> connectionClass = Class.forName("android.app.UiAutomationConnection");
    Constructor<?> connectionCtor = connectionClass.getDeclaredConstructor(); connectionCtor.setAccessible(true);
    Object connection = connectionCtor.newInstance();
    Constructor<?> ctor = UiAutomation.class.getDeclaredConstructor(Looper.class, Class.forName("android.app.IUiAutomationConnection"));
    ctor.setAccessible(true);
    automation = (UiAutomation)ctor.newInstance(thread.getLooper(), connection);
    // FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES. Never fall back to flags=0.
    try { UiAutomation.class.getMethod("connect", int.class).invoke(automation, 1); }
    catch (NoSuchMethodException e) { UiAutomation.class.getMethod("connectWithTimeout", int.class, long.class).invoke(automation, 1, 10000L); }
    AccessibilityServiceInfo info = automation.getServiceInfo();
    if (info == null) info = new AccessibilityServiceInfo();
    info.eventTypes = AccessibilityEvent.TYPES_ALL_MASK;
    info.flags |= AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
        | AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS | AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS;
    automation.setServiceInfo(info);
    automation.setOnAccessibilityEventListener(event -> dirty = true);
  }
  static void walk(Screen screen, AccessibilityNodeInfo node, int window, JSONArray nodes, StringBuilder tree, StringBuilder buttons) throws Exception {
    if (node == null || nodes.length() >= 10000) return;
    android.graphics.Rect r = new android.graphics.Rect(); node.getBoundsInScreen(r);
    String token = window + ":" + nodes.length();
    String label = node.isPassword() ? "" : text(node.getText());
    String description = text(node.getContentDescription());
    String resource = text(node.getViewIdResourceName());
    JSONObject item = new JSONObject();
    item.put("token",token).put("package",text(node.getPackageName())).put("window_id",window)
        .put("text",label).put("description",description).put("resource_id",resource)
        .put("class",text(node.getClassName())).put("enabled",node.isEnabled())
        .put("visible",node.isVisibleToUser()).put("clickable",node.isClickable())
        .put("editable",node.isEditable()).put("scrollable",node.isScrollable()).put("password",node.isPassword())
        .put("bounds",new JSONArray(Arrays.asList(r.left,r.top,r.right,r.bottom)));
    nodes.put(item); screen.nodes.put(token,node);
    tree.append("<node disp=\"").append(screen.display).append("\" text=\"").append(xml(label))
        .append("\" id=\"").append(xml(resource)).append("\" class=\"").append(xml(text(node.getClassName())))
        .append("\" desc=\"").append(xml(description)).append("\" clickable=\"").append(node.isClickable())
        .append("\" bounds=\"[").append(r.left).append(',').append(r.top).append("][").append(r.right).append(',').append(r.bottom)
        .append("]\" cx=\"").append(r.centerX()).append("\" cy=\"").append(r.centerY()).append("\"/>\n");
    if (node.isClickable() && node.isEnabled() && node.isVisibleToUser() && (!label.isEmpty() || !description.isEmpty())) {
      buttons.append(label.replace('\t',' ').replace('\n',' ')).append('\t')
          .append(description.replace('\t',' ').replace('\n',' ')).append('\t')
          .append(r.centerX()).append('\t').append(r.centerY()).append('\n');
    }
    for (int i=0;i<node.getChildCount();i++) walk(screen,node.getChild(i),window,nodes,tree,buttons);
  }
  static void refresh(Screen screen, SparseArray<List<AccessibilityWindowInfo>> all) throws Exception {
    release(screen);
    JSONArray nodes = new JSONArray(); StringBuilder tree = new StringBuilder(), buttons = new StringBuilder();
    List<AccessibilityWindowInfo> windows = all.get(screen.display);
    if (windows != null) for (AccessibilityWindowInfo window : windows) {
      AccessibilityNodeInfo root = window.getRoot();
      if (root != null) walk(screen,root,window.getId(),nodes,tree,buttons);
    }
    String fingerprint = nodes.toString();
    if (!fingerprint.equals(screen.fingerprint)) { screen.revision++; screen.fingerprint=fingerprint; }
    long now = System.currentTimeMillis();
    screen.snapshot = new JSONObject().put("display_id",screen.display).put("generation",screen.generation())
        .put("revision",screen.revision).put("observed_at_ms",now).put("valid",nodes.length()>0).put("nodes",nodes);
    // Empty observations INVALIDATE old targets. A heartbeat never makes old buttons fresh.
    write(new File(screen.dir,"snapshot.json"),screen.snapshot.toString());
    write(new File(screen.dir,"tree.xml"),tree.toString());
    write(new File(screen.dir,"btns.tsv"),buttons.toString());
    write(new File(screen.dir,"hb"),Long.toString(now));
  }
  static void requests(Screen screen) throws Exception {
    File[] files = screen.dir.listFiles((d,n) -> n.matches("request-[a-f0-9]{32}\\.json"));
    if (files == null) return;
    Arrays.sort(files,Comparator.comparing(File::getName));
    for (File file : files) {
      String requestId = file.getName().substring(8,40);
      JSONObject result = new JSONObject().put("request_id",requestId).put("ok",false).put("dispatched",false);
      try {
        JSONObject request = new JSONObject(read(file));
        // Consume before dispatch. A reader restart must never replay a queued action.
        if (!file.delete()) throw new IOException("could not consume request");
        refresh(screen,automation.getWindowsOnAllDisplays());
        if (request.optLong("deadline_ms",0) < System.currentTimeMillis()) throw new IllegalArgumentException("request expired");
        if (request.optInt("display_id",-1) != screen.display || screen.display <= 0
            || !screen.generation().equals(request.optString("generation"))
            || screen.revision != request.optLong("revision",-1)
            || !screen.snapshot.optBoolean("valid")) throw new IllegalArgumentException("snapshot changed");
        AccessibilityNodeInfo node = screen.nodes.get(request.optString("token"));
        if (node == null || !node.refresh() || !node.isEnabled() || !node.isVisibleToUser()
            || !text(node.getPackageName()).equals(request.optString("package"))) throw new IllegalArgumentException("target unavailable");
        String action = request.getString("action"); boolean ok;
        if (action.equals("click") && node.isClickable()) {
          result.put("dispatched",true); ok=node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
        } else if (action.equals("set_text") && node.isEditable()) {
          Bundle arguments = new Bundle(); arguments.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,request.getString("text"));
          result.put("dispatched",true); ok=node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,arguments);
        } else if ((action.equals("scroll_forward") || action.equals("scroll_backward")) && node.isScrollable()) {
          result.put("dispatched",true); ok=node.performAction(action.equals("scroll_forward") ? AccessibilityNodeInfo.ACTION_SCROLL_FORWARD : AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD);
        } else throw new IllegalArgumentException("unsupported action on this target");
        result.put("ok",ok); if (!ok) result.put("error","Android did not confirm action dispatch");
        dirty=true;
      } catch (Throwable error) { file.delete(); result.put("error",error.toString()); }
      write(new File(screen.dir,"response-"+requestId+".json"),result.toString());
    }
    // Bound abandoned response retention.
    File[] replies=screen.dir.listFiles((d,n)->n.matches("response-[a-f0-9]{32}\\.json"));
    if(replies!=null) for(File reply:replies) if(System.currentTimeMillis()-reply.lastModified()>60000) reply.delete();
  }
  static void updateTargets(File base) throws Exception {
    Set<String> live=new HashSet<>();
    File[] dirs=base.listFiles(File::isDirectory);
    if(dirs!=null) for(File dir:dirs) {
      if(!dir.getName().matches("[A-Za-z0-9_-]{1,64}")) continue;
      try {
        int id=Integer.parseInt(read(new File(dir,"id")).trim()); if(id<=0) continue;
        String name=dir.getName(); live.add(name); Screen old=screens.get(name);
        if(old==null || old.display!=id) { if(old!=null) release(old); screens.put(name,new Screen(name,id,dir)); dirty=true; }
      } catch(Exception ignored) {}
    }
    Iterator<Map.Entry<String,Screen>> iterator=screens.entrySet().iterator();
    while(iterator.hasNext()) { Map.Entry<String,Screen> entry=iterator.next(); if(!live.contains(entry.getKey())) {release(entry.getValue());iterator.remove();} }
  }
  public static void main(String[] args) throws Exception {
    boolean daemon=args.length>0 && args[0].equals("daemon");
    connect();
    try {
      if(!daemon) {
        int id=Integer.parseInt(args[0]);
        Screen one=new Screen("one",id,new File(System.getProperty("java.io.tmpdir","/data/local/tmp")));
        JSONArray nodes=new JSONArray(); StringBuilder tree=new StringBuilder(),buttons=new StringBuilder();
        List<AccessibilityWindowInfo> wins=automation.getWindowsOnAllDisplays().get(id);
        if(wins!=null) for(AccessibilityWindowInfo win:wins) walk(one,win.getRoot(),win.getId(),nodes,tree,buttons);
        System.out.print(tree); release(one); return;
      }
      if(args.length<3 || !args[1].equals("all")) throw new IllegalArgumentException("use UD daemon all /data/local/tmp/vd");
      File base=new File(args[2]); base.mkdirs();
      write(new File(base,"ud.pid"),new File("/proc/self").getCanonicalFile().getName());
      long last=0; int empty=0;
      while(true) {
        if(!base.exists()) break;
        updateTargets(base);
        if(screens.isEmpty()) { if(++empty>=12) break; } else empty=0;
        long now=System.currentTimeMillis();
        if((dirty && now-last>=150) || now-last>=750) {
          dirty=false;last=now;
          SparseArray<List<AccessibilityWindowInfo>> all=automation.getWindowsOnAllDisplays();
          for(Screen screen:screens.values()) {
            try { refresh(screen,all); }
            catch(Throwable error) {
              release(screen);
              screen.revision++;
              screen.snapshot=new JSONObject().put("display_id",screen.display).put("generation",screen.generation())
                  .put("revision",screen.revision).put("observed_at_ms",now).put("valid",false).put("nodes",new JSONArray());
              write(new File(screen.dir,"snapshot.json"),screen.snapshot.toString());
              write(new File(screen.dir,"tree.xml"),"");write(new File(screen.dir,"btns.tsv"),"");
            }
          }
        }
        for(Screen screen:screens.values()) requests(screen);
        write(new File(base,"hb"),Long.toString(System.currentTimeMillis()));
        Thread.sleep(80);
      }
    } finally {
      for(Screen screen:screens.values()) release(screen);
      try { UiAutomation.class.getMethod("disconnect").invoke(automation); } catch(Throwable ignored) {}
      System.exit(0);
    }
  }
}