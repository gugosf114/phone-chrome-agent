import java.lang.reflect.*;
import android.os.Looper;
import android.os.Handler;

public class VD {
  static java.io.PrintWriter L;
  static void log(String s){ try{ L.println(s); L.flush(); }catch(Throwable t){} }
  public static void main(String[] a) throws Exception {
    new java.io.File("/data/local/tmp/vd").mkdirs();
    L=new java.io.PrintWriter(new java.io.FileWriter("/data/local/tmp/vd/dbg.log",true));
    try{ run(a); }catch(Throwable t){ Throwable c=(t instanceof InvocationTargetException)?t.getCause():t; log("FATAL "+c); if(c!=null)for(StackTraceElement e:c.getStackTrace())log("  at "+e); }
  }
  static void run(String[] a) throws Exception {
    int w=a.length>0?Integer.parseInt(a[0]):1080, h=a.length>1?Integer.parseInt(a[1]):2400, dpi=a.length>2?Integer.parseInt(a[2]):420;
    final String fd=a.length>3?a[3]:"/data/local/tmp/vd";
    Looper.prepareMainLooper();
    Class<?> IR=Class.forName("android.media.ImageReader");
    final Object reader=IR.getMethod("newInstance",int.class,int.class,int.class,int.class).invoke(null,w,h,1,2);
    Object surface=IR.getMethod("getSurface").invoke(reader);
    Class<?> ATh=Class.forName("android.app.ActivityThread");
    Object at=ATh.getMethod("systemMain").invoke(null);
    android.content.Context sys=(android.content.Context)ATh.getMethod("getSystemContext").invoke(at);
    android.content.Context ctx=sys.createPackageContext("com.android.shell",0);
    Object dm=ctx.getSystemService("display");
    Class<?> DM=Class.forName("android.hardware.display.DisplayManager");
    int F_PUBLIC=(Integer)DM.getField("VIRTUAL_DISPLAY_FLAG_PUBLIC").get(null);
    int F_PRES=(Integer)DM.getField("VIRTUAL_DISPLAY_FLAG_PRESENTATION").get(null);
    int F_TRUST; try{F_TRUST=(Integer)DM.getField("VIRTUAL_DISPLAY_FLAG_TRUSTED").get(null);}catch(Throwable t){F_TRUST=1<<10;}
    int F_DECOR; try{F_DECOR=(Integer)DM.getField("VIRTUAL_DISPLAY_FLAG_SHOULD_SHOW_SYSTEM_DECORATIONS").get(null);}catch(Throwable t){F_DECOR=0;}
    // Let apps launch + draw on this display even while the phone is locked (keyguard up),
    // so the hidden lane is truly always-on. Without it, `am start --display` is denied
    // with a SecurityException whenever the lock screen is showing. NOTE: this flag is
    // rejected together with FLAG_PUBLIC ("Public display must not be marked as
    // SHOW_WHEN_LOCKED_INSECURE"), so we drop PUBLIC and match the real cover display's
    // flag set (PRESENTATION | DECORATIONS | TRUSTED | INSECURE_KEYGUARD).
    int F_KG; try{F_KG=(Integer)DM.getField("VIRTUAL_DISPLAY_FLAG_CAN_SHOW_WITH_INSECURE_KEYGUARD").get(null);}catch(Throwable t){F_KG=1<<5;}
    // OWN_FOCUS gives this display its own, independent focus (so its app window becomes
    // the focused/interactive window there and the accessibility tree exposes its
    // buttons) WITHOUT stealing the real screen's focus. It is IGNORED unless the display
    // is in its own display group, so we also set OWN_DISPLAY_GROUP. Both require TRUSTED.
    int F_OF;  try{F_OF =(Integer)DM.getField("VIRTUAL_DISPLAY_FLAG_OWN_FOCUS").get(null);}catch(Throwable t){F_OF=1<<14;}
    int F_ODG; try{F_ODG=(Integer)DM.getField("VIRTUAL_DISPLAY_FLAG_OWN_DISPLAY_GROUP").get(null);}catch(Throwable t){F_ODG=1<<11;}
    if(F_PUBLIC<0){} // silence unused
    Object vd=DM.getMethod("createVirtualDisplay",String.class,int.class,int.class,int.class,android.view.Surface.class,int.class)
              .invoke(dm,"cover-hidden",w,h,dpi,(android.view.Surface)surface,F_PRES|F_TRUST|F_DECOR|F_KG|F_OF|F_ODG);
    Object disp=vd.getClass().getMethod("getDisplay").invoke(vd);
    int id=(Integer)disp.getClass().getMethod("getDisplayId").invoke(disp);
    // publish the id where the shell can read it, atomically
    java.io.PrintWriter idw=new java.io.PrintWriter(fd+"/id"); idw.println(id); idw.close();
    log("VD_DISPLAY_ID="+id); System.out.println("VD_DISPLAY_ID="+id); System.out.flush();
    final int W=w,H=h; final Method acq=IR.getMethod("acquireLatestImage");
    final java.io.File req=new java.io.File(fd+"/req");
    Handler hdl=new Handler(Looper.myLooper());
    hdl.post(new Runnable(){ public void run(){
      try{
        if(req.exists()){
          Object img=acq.invoke(reader);
          if(img!=null){
            Object[] pl=(Object[])img.getClass().getMethod("getPlanes").invoke(img); Object p0=pl[0];
            java.nio.ByteBuffer b=(java.nio.ByteBuffer)p0.getClass().getMethod("getBuffer").invoke(p0);
            int stride=(Integer)p0.getClass().getMethod("getRowStride").invoke(p0);
            byte[] by=new byte[b.remaining()]; b.get(by);
            java.io.FileOutputStream fo=new java.io.FileOutputStream(fd+"/frame.raw"); fo.write(by); fo.close();
            java.io.PrintWriter pw=new java.io.PrintWriter(fd+"/frame.meta"); pw.println(W+" "+H+" "+stride); pw.close();
            img.getClass().getMethod("close").invoke(img);
            new java.io.File(fd+"/frame.ready").createNewFile();
          } else {
            // no new image yet — drain nothing; try again next tick without clearing req
          }
          req.delete();
        }
      }catch(Throwable t){ log("cap err "+t); try{req.delete();}catch(Throwable e){} }
      hdl.postDelayed(this,120);
    }});
    log("ready (on-demand capture)"); Looper.loop();
  }
}
